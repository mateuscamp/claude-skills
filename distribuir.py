#!/usr/bin/env python3
"""Distribui as skills a partir de uma fonte só: o ref (por padrão `main`) deste repositório.

Skill é toda pasta de primeiro nível do ref que tem `SKILL.md`. Sem opção, gera em
`--destino` (por padrão `~/Documentos/Skills`), para cada skill:

- `<skill>.zip`, de `git archive --format=zip --prefix=<skill>/ <ref>:<skill>`;
- `<skill>.skill/<skill>/`, de `git archive --prefix=<skill>/ <ref>:<skill> | tar -x`;
- `code-audit-skill.md`, cópia do `SKILL.md` da code-audit.

O que difere é sobrescrito, sem guardar o anterior: toda versão está no histórico do git. Um
`<nome>.antigo` deixado por versões anteriores deste script sai. Não toca em nenhuma outra entrada
do destino.

As Gerais são lições com uma fonte na raiz e uma cópia igual em cada skill que as usa (cada skill
sai num zip próprio, então a cópia mora dentro dela), uma linha de SHARED_LESSONS para cada:

- Gerais de jogo: a fonte `gerais-de-jogo.md`, copiada para `<skill>/references/gerais-de-jogo.md`
  de cada skill de GENERAL_LESSONS_SKILLS (as de motor);
- Gerais de Lua: a fonte `gerais-de-lua.md`, copiada para `<skill>/references/gerais-de-lua.md` de
  cada skill de LUA_LESSONS_SKILLS (as de motor em Lua: a Godot não a recebe).

`--copiar-gerais` só regrava, na árvore de trabalho de `--repo`, as cópias de todas as Gerais a
partir das fontes da raiz; a cópia que virou symlink volta a ser arquivo. Recusa o checkout que
está no ref e o HEAD desanexado, porque a lição entra numa worktree em ramo próprio, e recusa sem
escrever nenhuma cópia se falta uma fonte ou a pasta de uma skill.

`--check-gerais` só confere as Gerais, como o item delas no `--check`, no ref (aqui o padrão é o
HEAD de `--repo`), e sai com 1 listando cada problema: é o que se roda no ramo, antes do PR. A
geração confere o mesmo antes de escrever qualquer coisa e recusa se houver problema.

`--check` só lê e sai com 1 listando cada problema:

- cópia do destino diferente do ref (zip por conteúdo dos membros, pasta pela árvore, `.md` pelo
  conteúdo), ou ausente;
- Gerais de jogo e de Lua, lidas no ref: cópia ausente, diferente da fonte ou symlink; cópia fora
  das skills da lista dela; linha de lição na seção velha de um `.md` dessas skills ("## Gerais de
  jogo"; "## Gerais de Lua" ou "## Lua:"), que ficou só com o ponteiro, e item da fonte repetido
  num deles;
- checkout de `--repo` fora do ref ou com mudança local, ou o ref atrás de `origin/<ref>` (só
  refs locais, sem rede);
- skill sem symlink `<links>/<skill>` que resolva para `<repo>/<skill>` (o Codex acha a skill por
  esse link; a pasta inteira como link arrasta o `synced/` do app e duplica skills);
- descrição do `SKILL.md` acima de 1.024 caracteres (o Codex 0.163.0 corta ali, calado).

Uso: rode depois de cada merge no main; rode `--check` antes de subir um zip no claude.ai; rode
`--repo <worktree> --copiar-gerais` depois de editar o `gerais-de-jogo.md` ou o `gerais-de-lua.md`,
antes do commit, e `--repo <worktree> --check-gerais` depois do commit, antes do PR.
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from typing import NamedTuple

CODEX_DESCRIPTION_MAX = 1024
# Skill que também sai como .md solto no destino, com o nome que o documento de origem tinha.
LOOSE_MARKDOWN = {"code-audit": "code-audit-skill.md"}
# Cópia anterior que este script guardava até 2026-11-01; o git já guarda toda versão.
LEGACY_BACKUP_SUFFIX = ".antigo"
# Lições de jogo que valem em qualquer engine: uma fonte na raiz e uma cópia igual em cada skill
# de motor. A lista é explícita: skill de motor nova entra acrescentando o nome aqui.
GENERAL_LESSONS_SOURCE = "gerais-de-jogo.md"
GENERAL_LESSONS_COPY = "references/gerais-de-jogo.md"
GENERAL_LESSONS_SKILLS = ("ai-first-defold", "ai-first-godot", "ai-first-love")
# A seção que o armadilhas.md das skills de motor tinha antes da fonte única. Ficou só com o
# ponteiro, em prosa: item de lista ou subtítulo nela é lição escrita no lugar velho, ou a seção
# inteira de volta por um merge com um ramo anterior à fonte única.
GENERAL_LESSONS_OLD_SECTION = "## Gerais de jogo"
# Lições da linguagem Lua comuns às skills de motor em Lua (as diferenças entre o LuaJIT do jogo e o
# Lua 5.x da suíte): a mesma forma, só nas skills que usam Lua. O nome da fonte é fixo: o AGENTS.md
# dos projetos o cita. A seção velha tinha o título "## Lua: LuaJIT do <jogo|motor> e Lua 5.x da
# suíte", e o ponteiro novo é "## Gerais de Lua"; os dois prefixos levam o ':' ou o "Gerais de",
# para não pegar a "## LuaLS e anotações" do motor.
LUA_LESSONS_SOURCE = "gerais-de-lua.md"
LUA_LESSONS_COPY = "references/gerais-de-lua.md"
LUA_LESSONS_SKILLS = ("ai-first-defold", "ai-first-love")
LUA_LESSONS_OLD_SECTIONS = ("## Gerais de Lua", "## Lua:")
LESSON_LINE = re.compile(r"([-*+]|\d+[.)]|#{3,})\s")
NEXT_SECTION = re.compile(r"#{1,2}\s")


class Shared(NamedTuple):
    """Uma fonte de Gerais: a fonte na raiz, a cópia em cada skill da lista e a seção velha."""
    title: str
    source: str
    copy: str
    skills: tuple
    skills_name: str
    old_sections: tuple


SHARED_LESSONS = (
    Shared("Gerais de jogo", GENERAL_LESSONS_SOURCE, GENERAL_LESSONS_COPY, GENERAL_LESSONS_SKILLS,
           "GENERAL_LESSONS_SKILLS", (GENERAL_LESSONS_OLD_SECTION,)),
    Shared("Gerais de Lua", LUA_LESSONS_SOURCE, LUA_LESSONS_COPY, LUA_LESSONS_SKILLS,
           "LUA_LESSONS_SKILLS", LUA_LESSONS_OLD_SECTIONS),
)


def git(repo, *args, check=True):
    """Roda git no repositório e devolve stdout em bytes; erro sai com a mensagem do git."""
    # Sem trava opcional: o `status` do --check não regrava o índice da pasta compartilhada.
    result = subprocess.run(["git", "--no-optional-locks", "-C", repo, *args], capture_output=True)
    if check and result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip()
        sys.exit(f"erro: git {' '.join(args)} saiu com {result.returncode}: {message}")
    return result


def git_text(repo, *args):
    return git(repo, *args).stdout.decode().strip()


def list_skills(repo, ref):
    """Pastas de primeiro nível do ref que têm SKILL.md, em ordem alfabética."""
    paths = git(repo, "ls-tree", "-r", "-z", "--name-only", ref).stdout.decode().split("\0")
    return sorted(p.split("/")[0] for p in paths if re.fullmatch(r"[^/]+/SKILL\.md", p))


def expected_tree(repo, ref, skill):
    """Arquivos da skill no ref: {caminho com o prefixo <skill>/: (conteúdo, executável)}."""
    tar_bytes = git(repo, "archive", "--format=tar", f"--prefix={skill}/", f"{ref}:{skill}").stdout
    tree = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as archive:
        for member in archive.getmembers():
            if member.issym():
                tree[member.name] = (member.linkname.encode(), False)
            elif member.isfile():
                content = archive.extractfile(member).read()
                tree[member.name] = (content, bool(member.mode & 0o100))
    return tree


def folder_tree(root):
    """Mesma forma de expected_tree para uma pasta do disco, com caminhos relativos a root."""
    tree = {}
    for current, dirs, files in os.walk(root):
        for name in files + [d for d in dirs if os.path.islink(os.path.join(current, d))]:
            path = os.path.join(current, name)
            relative = os.path.relpath(path, root).replace(os.sep, "/")
            if os.path.islink(path):
                tree[relative] = (os.readlink(path).encode(), False)
                continue
            with open(path, "rb") as handle:
                tree[relative] = (handle.read(), bool(os.stat(path).st_mode & 0o100))
    return tree


def zip_members(path):
    """{nome do membro: conteúdo} de um zip, sem as entradas de pasta."""
    with zipfile.ZipFile(path) as archive:
        return {i.filename: archive.read(i) for i in archive.infolist() if not i.is_dir()}


def differing_paths(expected, actual):
    """Caminhos que faltam, sobram ou diferem entre dois dicionários de árvore."""
    return sorted(p for p in set(expected) | set(actual) if expected.get(p) != actual.get(p))


def describe_paths(paths, limit=4):
    shown = ", ".join(paths[:limit])
    return shown + (f" e mais {len(paths) - limit}" if len(paths) > limit else "")


def compare_zip(path, tree):
    """None se o zip tem os mesmos membros e conteúdos do ref; senão o motivo."""
    if not os.path.isfile(path):
        return "ausente"
    try:
        actual = zip_members(path)
    except zipfile.BadZipFile as error:
        return f"zip ilegível ({error})"
    expected = {name: content for name, (content, _) in tree.items()}
    diff = differing_paths(expected, actual)
    return f"{len(diff)} membro(s) diferente(s): {describe_paths(diff)}" if diff else None


def compare_folder(path, tree):
    if not os.path.isdir(path):
        return "ausente"
    diff = differing_paths(tree, folder_tree(path))
    return f"{len(diff)} arquivo(s) diferente(s): {describe_paths(diff)}" if diff else None


def compare_file(path, content):
    if not os.path.isfile(path):
        return "ausente"
    with open(path, "rb") as handle:
        return None if handle.read() == content else "conteúdo diferente"


def ref_blob(repo, ref, path):
    """Conteúdo do arquivo `path` no ref, ou None se o ref não o tem como arquivo."""
    result = git(repo, "cat-file", "blob", f"{ref}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def ref_mode(repo, ref, path):
    """Modo de `path` no ref ('100644', '120000' para symlink...), ou None se não está lá."""
    entry = git(repo, "ls-tree", "-z", ref, "--", path).stdout.decode().rstrip("\0")
    return entry.split(" ", 1)[0] if entry else None


def tracked_paths(repo, ref):
    """Todo arquivo do ref, com o caminho a partir da raiz."""
    return [p for p in git(repo, "ls-tree", "-r", "-z", "--name-only", ref).stdout.decode().split("\0") if p]


def first_differing_line(expected, actual):
    """Número (a partir de 1) da primeira linha em que dois conteúdos diferem."""
    expected_lines, actual_lines = expected.split(b"\n"), actual.split(b"\n")
    for number, (wanted, found) in enumerate(zip(expected_lines, actual_lines), start=1):
        if wanted != found:
            return number
    return min(len(expected_lines), len(actual_lines)) + 1


# --- descrição no frontmatter YAML -------------------------------------------------------------

def frontmatter(text):
    """Linhas entre o '---' de abertura e o de fechamento, ou None se não há frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() in ("---", "..."):
            return lines[1:index]
    return None


def top_level_value(lines, key):
    """(resto da linha, linhas de continuação) da chave de primeiro nível, ou None."""
    for index, line in enumerate(lines):
        match = re.match(rf"{re.escape(key)}:(?:[ \t]+(.*))?$", line)
        if not match:
            continue
        continuation = []
        for following in lines[index + 1:]:
            if following.strip() and not following[0].isspace():
                break
            continuation.append(following)
        return (match.group(1) or "").rstrip(), continuation
    return None


def fold_lines(lines):
    """Dobra de escalar plano ou entre aspas: quebra vira espaço, linha vazia vira quebra."""
    text, pending = "", 0
    for line in (l.strip() for l in lines):
        if not line:
            pending += 1
            continue
        if text:
            text += "\n" * pending if pending else " "
        text += line
        pending = 0
    return text


def fold_block(body):
    """Dobra do escalar '>': linhas normais se juntam com espaço; linha mais indentada e linha
    vazia mantêm a quebra."""
    text, previous, pending = "", None, 0
    for line in body:
        if not line:
            pending += 1
            continue
        if previous is not None:
            indented = line[0] in " \t" or previous[0] in " \t"
            text += "\n" * (pending + 1) if indented else ("\n" * pending if pending else " ")
        text += line
        previous, pending = line, 0
    return text


def block_scalar(header, lines):
    """Escalar de bloco ('|' ou '>', com indicadores de corte e de indentação opcionais)."""
    match = re.fullmatch(r"([|>])([+-]?)(\d?)([+-]?)\s*(#.*)?", header)
    if not match:
        return None
    style, chomp, explicit = match.group(1), match.group(2) or match.group(4), match.group(3)
    filled = [l for l in lines if l.strip()]
    if not filled:
        return ""
    indent = int(explicit) if explicit else len(filled[0]) - len(filled[0].lstrip())
    body = [l[indent:] if l.strip() else "" for l in lines]
    trailing = 0
    while body and not body[-1]:
        body.pop()
        trailing += 1
    text = "\n".join(body) if style == "|" else fold_block(body)
    if chomp == "-":
        return text
    return text + "\n" * (1 + trailing if chomp == "+" else 1)


DOUBLE_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\", '"': '"', "/": "/", " ": " "}
HEX_ESCAPES = {"x": 2, "u": 4, "U": 8}


def quoted_scalar(first, lines):
    """Escalar entre aspas simples ou duplas; em várias linhas, as quebras se dobram com espaço
    (aproximação: o espaço logo depois da aspa de abertura de um valor em várias linhas some)."""
    quote, body = first[0], first[1:]
    if lines:
        body = fold_lines([body] + lines)
    text, index = "", 0
    while index < len(body):
        char = body[index]
        if quote == "'" and char == "'":
            if body[index + 1:index + 2] != "'":
                break
            text, index = text + "'", index + 2
            continue
        if quote == '"' and char == '"':
            break
        if quote == '"' and char == "\\" and index + 1 < len(body):
            code = body[index + 1]
            width = HEX_ESCAPES.get(code, 0)
            hex_digits = body[index + 2:index + 2 + width]
            text += chr(int(hex_digits, 16)) if width else DOUBLE_ESCAPES.get(code, code)
            index += 2 + width
            continue
        text, index = text + char, index + 1
    return text


def plain_scalar(first, lines):
    """Escalar plano: o comentário começa em ' #'; as continuações se dobram com espaço."""
    pieces = []
    for line in [first] + lines:
        comment = re.search(r"(^|\s)#", line)
        pieces.append(line[:comment.start()] if comment else line)
        if comment:
            break
    return fold_lines(pieces)


def description_of(skill_md):
    """Descrição do frontmatter de um SKILL.md, ou None se não houver."""
    lines = frontmatter(skill_md)
    found = top_level_value(lines, "description") if lines is not None else None
    if found is None:
        return None
    first, continuation = found
    if first[:1] in ("|", ">"):
        return block_scalar(first, continuation)
    if first[:1] in ("'", '"'):
        return quoted_scalar(first, continuation)
    return plain_scalar(first, continuation)


# --- verificações do --check -------------------------------------------------------------------

def check_copies(repo, ref, skills, destination):
    problems = []
    for skill in skills:
        tree = expected_tree(repo, ref, skill)
        targets = [
            (f"{skill}.zip", compare_zip(os.path.join(destination, f"{skill}.zip"), tree)),
            (f"{skill}.skill/", compare_folder(os.path.join(destination, f"{skill}.skill"), tree)),
        ]
        if skill in LOOSE_MARKDOWN:
            name = LOOSE_MARKDOWN[skill]
            content = tree[f"{skill}/SKILL.md"][0]
            targets.append((name, compare_file(os.path.join(destination, name), content)))
        problems += [f"{os.path.join(destination, n)} difere do {ref}: {why}" for n, why in targets if why]
    return problems


def check_general_lessons(repo, ref):
    """Problemas de todas as Gerais (de SHARED_LESSONS) no ref, não na árvore."""
    paths = tracked_paths(repo, ref)
    problems = []
    for shared in SHARED_LESSONS:
        problems += check_shared(repo, ref, paths, shared)
    return problems


def check_shared(repo, ref, paths, shared):
    """Problemas de uma Gerais no ref: as cópias, a cópia fora da lista e a lição escrita fora da
    fonte."""
    source = ref_blob(repo, ref, shared.source)
    if source is None:
        return [f"{shared.source} não existe no {ref}: é a fonte das cópias de {', '.join(shared.skills)}"]
    problems = [copy_problem(repo, ref, skill, source, shared) for skill in shared.skills]
    problems = [p for p in problems if p]
    problems += orphan_copies(ref, paths, shared)
    problems += lessons_outside_source(repo, ref, paths, source, shared)
    return problems


def copy_problem(repo, ref, skill, source, shared):
    """Cópia da skill ausente, symlink ou diferente da fonte; None se igual."""
    path = f"{skill}/{shared.copy}"
    if ref_mode(repo, ref, path) == "120000":
        # O zip levaria o link quebrado, e o --copiar-gerais o desfaz.
        why = "é symlink, esperado arquivo"
    else:
        copy = ref_blob(repo, ref, path)
        if copy == source:
            return None
        why = "não existe" if copy is None else f"difere a partir da linha {first_differing_line(source, copy)}"
    return (f"{path} no {ref} {why}; a fonte é {shared.source}: regrave com "
            f"`distribuir.py --repo <worktree> --copiar-gerais` e faça commit")


def orphan_copies(ref, paths, shared):
    """Arquivo com o nome da fonte fora da raiz e das cópias esperadas: o --check não o compara."""
    expected = {shared.source} | {f"{s}/{shared.copy}" for s in shared.skills}
    return [f"{p} no {ref} é cópia das {shared.title} fora das skills de {shared.skills_name} "
            f"({', '.join(shared.skills)}): acrescente a skill à lista ou apague a cópia"
            for p in paths if p.rsplit("/", 1)[-1] == shared.source and p not in expected]


def old_section_lines(lines, old_sections):
    """Números (a partir de 1) das linhas de lição dentro de uma seção que começa por um dos títulos
    de old_sections."""
    prefixes = tuple(title.encode() for title in old_sections)
    found, inside = [], False
    for number, line in enumerate(lines, start=1):
        if line.startswith(prefixes):
            inside = True
        elif NEXT_SECTION.match(line.decode(errors="replace")):
            inside = False
        elif inside and LESSON_LINE.match(line.decode(errors="replace")):
            found.append(number)
    return found


def lessons_outside_source(repo, ref, paths, source, shared):
    """Lição nos `.md` das skills da lista fora da cópia: no lugar velho da seção, ou item da fonte
    repetido. Um problema por arquivo; as cópias de todas as Gerais ficam de fora."""
    items = {line for line in source.split(b"\n") if line.startswith(b"- ")}
    copies = {s.source for s in SHARED_LESSONS}
    sections = " ou ".join(f"\"{title}\"" for title in shared.old_sections)
    problems = []
    for path in paths:
        name = path.rsplit("/", 1)[-1]
        skill_markdown = path.split("/")[0] in shared.skills and name.endswith(".md")
        if not skill_markdown or name in copies:
            continue
        lines = (ref_blob(repo, ref, path) or b"").split(b"\n")
        in_section = old_section_lines(lines, shared.old_sections)
        repeated = [n for n, line in enumerate(lines, start=1) if line in items]
        if in_section:
            same = f", {len(repeated)} igual(is) a item da fonte" if repeated else ""
            problems.append(f"{path} no {ref} tem {len(in_section)} linha(s) de lição na seção "
                            f"{sections} (a primeira na linha {in_section[0]}{same}); a seção é só o "
                            f"ponteiro das {shared.title}: a lição se escreve em {shared.source}, na "
                            f"raiz, e o --copiar-gerais a copia")
        elif repeated:
            problems.append(f"{path} no {ref} repete {len(repeated)} item(ns) do {shared.source} "
                            f"(o primeiro na linha {repeated[0]}); a lição mora só na fonte e nas cópias")
    return problems


def check_checkout(repo, ref):
    problems = []
    branch = git(repo, "symbolic-ref", "-q", "--short", "HEAD", check=False).stdout.decode().strip()
    is_branch = git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{ref}", check=False).returncode == 0
    head = git_text(repo, "rev-parse", "HEAD")
    target = git_text(repo, "rev-parse", f"{ref}^{{commit}}")
    if is_branch and branch != ref:
        where = f"no ramo {branch}" if branch else f"desanexado em {head[:7]}"
        problems.append(f"o checkout de {repo} está {where}, não no {ref}: toda sessão local carrega "
                        f"o que está em checkout")
    elif not is_branch and head != target:
        problems.append(f"o checkout de {repo} está em {head[:7]}, não no {ref} ({target[:7]})")
    dirty = git_text(repo, "status", "--porcelain")
    if dirty:
        count = len(dirty.splitlines())
        problems.append(f"o checkout de {repo} tem {count} mudança(s) local(is) fora do commit: "
                        f"lição entra numa worktree, não na pasta compartilhada")
    return problems


def check_remote(repo, ref):
    """(problemas, nota): só compara com o origin/<ref> local, sem ir à rede."""
    remote = f"refs/remotes/origin/{ref}"
    if git(repo, "show-ref", "--verify", "--quiet", remote, check=False).returncode != 0:
        return [], f"nota: não há origin/{ref} local; o atraso em relação ao GitHub não foi conferido"
    behind = int(git_text(repo, "rev-list", "--count", f"{ref}..origin/{ref}"))
    note = (f"nota: {ref} comparado com o origin/{ref} local, sem rede; rode "
            f"`git -C {repo} fetch` antes para comparar com o GitHub")
    if behind:
        return [f"{ref} está {behind} commit(s) atrás de origin/{ref}"], note
    return [], note


def check_links(repo, skills, links):
    problems = []
    if os.path.realpath(links) == os.path.realpath(repo):
        problems.append(f"{links} é link para a pasta inteira {repo}: arrasta o synced/ e duplica "
                        f"skills; use um symlink por skill")
        return problems
    for skill in skills:
        link, source = os.path.join(links, skill), os.path.join(repo, skill)
        if not os.path.islink(link):
            kind = "é uma cópia, não um symlink" if os.path.exists(link) else "não existe"
            problems.append(f"{link} {kind}: o Codex não vê a skill {skill} da fonte")
        elif os.path.realpath(link) != os.path.realpath(source):
            problems.append(f"{link} aponta para {os.path.realpath(link)}, não para {source}")
    return problems


def check_descriptions(repo, ref, skills):
    problems, lengths = [], {}
    for skill in skills:
        text = git(repo, "show", f"{ref}:{skill}/SKILL.md").stdout.decode()
        description = description_of(text)
        if description is None:
            problems.append(f"{skill}/SKILL.md no {ref} não tem description no frontmatter")
            continue
        lengths[skill] = len(description)
        if len(description) > CODEX_DESCRIPTION_MAX:
            problems.append(f"{skill}/SKILL.md: description com {len(description)} caracteres, "
                            f"acima de {CODEX_DESCRIPTION_MAX} (o Codex 0.163.0 corta o resto calado)")
    return problems, lengths


def run_check(args, skills):
    problems = check_copies(args.repo, args.ref, skills, args.destino)
    problems += check_general_lessons(args.repo, args.ref)
    problems += check_checkout(args.repo, args.ref)
    remote_problems, note = check_remote(args.repo, args.ref)
    problems += remote_problems
    problems += check_links(args.repo, skills, args.links)
    description_problems, lengths = check_descriptions(args.repo, args.ref, skills)
    problems += description_problems
    print("descrições: " + ", ".join(f"{s} {n}" for s, n in lengths.items()))
    print_problems(problems)
    print(note)
    return verdict(problems)


def print_problems(problems):
    for problem in problems:
        print(f"PROBLEMA: {problem}")


def verdict(problems):
    if problems:
        print(f"{len(problems)} problema(s).")
        return 1
    print("tudo em dia.")
    return 0


def run_check_general(args):
    """Só as Gerais no ref; o resto do --check (destino, links, checkout) não vale no ramo."""
    problems = check_general_lessons(args.repo, args.ref)
    print_problems(problems)
    sources = [s.source for s in SHARED_LESSONS]
    skills = sorted({skill for s in SHARED_LESSONS for skill in s.skills})
    local = git_text(args.repo, "status", "--porcelain", "--", *sources, *skills)
    if local:
        print(f"nota: {len(local.splitlines())} mudança(s) local(is) fora do commit em "
              f"{' ou '.join(sources)} ou nas skills das listas; o --check-gerais confere o {args.ref}, "
              f"não a árvore")
    return verdict(problems)


# --- geração -----------------------------------------------------------------------------------

def remove_entry(path):
    """Apaga uma entrada deste script no destino: arquivo, link ou pasta (sem seguir link)."""
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def remove_legacy_backup(final):
    """Apaga o final.antigo que versões anteriores deste script deixaram."""
    backup = final + LEGACY_BACKUP_SUFFIX
    if os.path.lexists(backup):
        remove_entry(backup)
        print(f"apagado: {backup}")


def install(new_path, final, workdir):
    """Põe new_path em final; o que havia em final vai para a pasta de trabalho e sai com ela."""
    remove_legacy_backup(final)
    if os.path.lexists(final):
        # Renomear em vez de apagar antes: final nunca fica ausente por mais que dois renames.
        os.rename(final, os.path.join(workdir, os.path.basename(final) + ".anterior"))
    os.rename(new_path, final)
    print(f"escrito: {final}")


def generate_zip(args, skill, tree, workdir):
    final = os.path.join(args.destino, f"{skill}.zip")
    if compare_zip(final, tree) is None:
        remove_legacy_backup(final)
        print(f"igual: {final}")
        return
    new_path = os.path.join(workdir, f"{skill}.zip")
    content = git(args.repo, "archive", "--format=zip", f"--prefix={skill}/", f"{args.ref}:{skill}").stdout
    with open(new_path, "wb") as handle:
        handle.write(content)
    install(new_path, final, workdir)


def generate_folder(args, skill, tree, workdir):
    final = os.path.join(args.destino, f"{skill}.skill")
    if compare_folder(final, tree) is None:
        remove_legacy_backup(final)
        print(f"igual: {final}")
        return
    new_path = os.path.join(workdir, f"{skill}.skill")
    os.mkdir(new_path)
    command = ["git", "--no-optional-locks", "-C", args.repo, "archive",
               f"--prefix={skill}/", f"{args.ref}:{skill}"]
    archive = subprocess.Popen(command, stdout=subprocess.PIPE)
    extract = subprocess.run(["tar", "-x", "-f", "-", "-C", new_path], stdin=archive.stdout)
    archive.stdout.close()
    if archive.wait() != 0 or extract.returncode != 0:
        sys.exit(f"erro: git archive | tar -x da skill {skill} falhou")
    install(new_path, final, workdir)


def generate_markdown(args, skill, tree, workdir):
    name = LOOSE_MARKDOWN[skill]
    final, content = os.path.join(args.destino, name), tree[f"{skill}/SKILL.md"][0]
    if compare_file(final, content) is None:
        remove_legacy_backup(final)
        print(f"igual: {final}")
        return
    new_path = os.path.join(workdir, name)
    with open(new_path, "wb") as handle:
        handle.write(content)
    install(new_path, final, workdir)


def run_generate(args, skills):
    problems = check_general_lessons(args.repo, args.ref)
    if problems:
        # O zip levaria a cópia divergente ou a lição duplicada para o claude.ai, calado.
        print_problems(problems)
        sys.exit(f"erro: nada foi escrito em {args.destino}: {len(problems)} problema(s) nas Gerais do "
                 f"{args.ref}, acima; conserte num ramo e confira com --check-gerais")
    os.makedirs(args.destino, exist_ok=True)
    # A pasta de trabalho fica dentro do destino para o rename ser atômico; é nossa e sai no fim.
    workdir = tempfile.mkdtemp(prefix=".distribuir-", dir=args.destino)
    try:
        for skill in skills:
            tree = expected_tree(args.repo, args.ref, skill)
            generate_zip(args, skill, tree, workdir)
            generate_folder(args, skill, tree, workdir)
            if skill in LOOSE_MARKDOWN:
                generate_markdown(args, skill, tree, workdir)
    finally:
        shutil.rmtree(workdir)
    remote_problems, note = check_remote(args.repo, args.ref)
    for problem in remote_problems:
        print(f"aviso: {problem}")
    print(note)
    return 0


# --- cópias das Gerais -------------------------------------------------------------------------

def general_lessons_sources(args):
    """[(Gerais, conteúdo da fonte na árvore de trabalho)] de SHARED_LESSONS; sai com erro antes de
    escrever qualquer cópia se o checkout está no ref ou desanexado, se falta uma fonte ou se falta
    a pasta de alguma skill."""
    branch = git(args.repo, "symbolic-ref", "-q", "--short", "HEAD", check=False).stdout.decode().strip()
    if not branch or branch == args.ref:
        # A pasta que toda sessão carrega fica no main e sem mudança local (README); desanexado no
        # commit do main, o nome do ramo não a distinguiria.
        head = git_text(args.repo, "rev-parse", "--short", "HEAD")
        where = f"no {args.ref}" if branch else f"desanexado em {head}"
        sys.exit(f"erro: --copiar-gerais escreve na árvore de trabalho de {args.repo}, que está {where}; "
                 f"a lição entra numa worktree em ramo próprio: passe --repo <worktree>")
    sources = []
    for shared in SHARED_LESSONS:
        source = os.path.join(args.repo, shared.source)
        if not os.path.isfile(source):
            sys.exit(f"erro: a fonte {source} não existe; esperado {shared.source} na raiz de --repo; "
                     f"nenhuma cópia foi escrita")
        missing = [s for s in shared.skills if not os.path.isdir(os.path.join(args.repo, s))]
        if missing:
            sys.exit(f"erro: sem a pasta da skill {', '.join(missing)} em {args.repo}; esperado uma pasta "
                     f"para cada nome de {shared.skills_name} ({', '.join(shared.skills)}); nenhuma "
                     f"cópia foi escrita")
        with open(source, "rb") as handle:
            sources.append((shared, handle.read()))
    return sources


def run_copy_general(args):
    """Regrava, na árvore de trabalho de --repo, as cópias de todas as Gerais a partir das fontes."""
    written = 0
    for shared, content in general_lessons_sources(args):
        written += copy_shared(args.repo, shared, content)
    if written:
        print("nota: só a árvore de trabalho mudou; o --check confere o commit")
    return 0


def copy_shared(repo, shared, content):
    """Regrava a cópia de cada skill da lista que difere da fonte; devolve quantas escreveu."""
    written = 0
    for skill in shared.skills:
        target = os.path.join(repo, skill, shared.copy)
        was_link = os.path.islink(target)
        if was_link:
            # O link seria seguido na comparação e na escrita, e iria quebrado no zip.
            os.remove(target)
        elif compare_file(target, content) is None:
            print(f"igual: {target}")
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(content)
        print(f"escrito: {target}" + (" (era symlink)" if was_link else ""))
        written += 1
    return written


def refuse_destination(repo, destination):
    """O destino não pode ser o repositório, ficar dentro dele nem acima dele."""
    repo_real, destination_real = os.path.realpath(repo), os.path.realpath(destination)
    inside = os.path.commonpath([repo_real, destination_real])
    if inside in (repo_real, destination_real):
        sys.exit(f"erro: --destino {destination} não pode ser o repositório {repo}, nem ficar dentro "
                 f"ou acima dele; esperado uma pasta fora do repositório")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", default="~/.claude/skills", help="repositório das skills")
    parser.add_argument("--ref", help="ref que é a fonte (padrão: main; com --check-gerais, HEAD)")
    parser.add_argument("--destino", default="~/Documentos/Skills", help="pasta dos zips e cópias")
    parser.add_argument("--links", default="~/.agents/skills", help="pasta dos symlinks do Codex")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="só confere; sai com 1 se houver problema")
    mode.add_argument("--copiar-gerais", action="store_true",
                      help="só regrava as cópias das Gerais (" + "; ".join(
                          f"<skill>/{s.copy} a partir do {s.source}" for s in SHARED_LESSONS)
                      + ") na árvore de trabalho de --repo")
    mode.add_argument("--check-gerais", action="store_true",
                      help="só confere as Gerais de jogo e de Lua no ref (padrão: HEAD); sai com 1 se "
                           "houver problema")
    args = parser.parse_args(argv)
    if args.ref is None:
        args.ref = "HEAD" if args.check_gerais else "main"
    for name in ("repo", "destino", "links"):
        setattr(args, name, os.path.abspath(os.path.expanduser(getattr(args, name))))
    return args


def main(argv):
    args = parse_args(argv)
    if args.copiar_gerais:
        return run_copy_general(args)
    resolved = git(args.repo, "rev-parse", "--verify", "--quiet", f"{args.ref}^{{commit}}", check=False)
    if resolved.returncode:
        detail = resolved.stderr.decode(errors="replace").strip()
        suffix = f" ({detail})" if detail else ""
        sys.exit(f"erro: --ref {args.ref} não é um commit de {args.repo}{suffix}")
    if args.check_gerais:
        shared = "; ".join(f"{s.title}: {s.source} e as cópias de {', '.join(s.skills)}" for s in SHARED_LESSONS)
        print(f"fonte: {args.repo} @ {args.ref} ({git_text(args.repo, 'rev-parse', '--short', args.ref)}); "
              f"{shared}")
        return run_check_general(args)
    refuse_destination(args.repo, args.destino)
    skills = list_skills(args.repo, args.ref)
    if not skills:
        sys.exit(f"erro: nenhuma pasta com SKILL.md no {args.ref} de {args.repo}")
    print(f"fonte: {args.repo} @ {args.ref} ({git_text(args.repo, 'rev-parse', '--short', args.ref)}); "
          f"skills: {', '.join(skills)}")
    return run_check(args, skills) if args.check else run_generate(args, skills)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
