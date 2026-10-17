#!/usr/bin/env python3
"""Distribui as skills a partir de uma fonte só: o ref (por padrão `main`) deste repositório.

Skill é toda pasta de primeiro nível do ref que tem `SKILL.md`. Sem opção, gera em
`--destino` (por padrão `~/Documentos/Skills`), para cada skill:

- `<skill>.zip`, de `git archive --format=zip --prefix=<skill>/ <ref>:<skill>`;
- `<skill>.skill/<skill>/`, de `git archive --prefix=<skill>/ <ref>:<skill> | tar -x`;
- `code-audit-skill.md`, cópia do `SKILL.md` da code-audit.

Antes de trocar o que difere, guarda o anterior em `<nome>.antigo`; um `<nome>.antigo` que já
exista sai, feito por este script ou à mão. Não toca em nenhuma outra entrada do destino.

`--copiar-gerais` só regrava, na árvore de trabalho de `--repo`, a cópia
`<skill>/references/gerais-de-jogo.md` de cada skill de GENERAL_LESSONS_SKILLS a partir da fonte
`gerais-de-jogo.md` da raiz (cada skill sai num zip próprio, então a cópia mora dentro dela).
Recusa o checkout que está no ref: a lição entra numa worktree em ramo próprio.

`--check` só lê e sai com 1 listando cada problema:

- cópia do destino diferente do ref (zip por conteúdo dos membros, pasta pela árvore, `.md` pelo
  conteúdo), ou ausente;
- cópia das Gerais de jogo ausente ou diferente da fonte, as duas lidas no ref;
- checkout de `--repo` fora do ref ou com mudança local, ou o ref atrás de `origin/<ref>` (só
  refs locais, sem rede);
- skill sem symlink `<links>/<skill>` que resolva para `<repo>/<skill>` (o Codex acha a skill por
  esse link; a pasta inteira como link arrasta o `synced/` do app e duplica skills);
- descrição do `SKILL.md` acima de 1.024 caracteres (o Codex 0.163.0 corta ali, calado).

Uso: rode depois de cada merge no main; rode `--check` antes de subir um zip no claude.ai; rode
`--repo <worktree> --copiar-gerais` depois de editar o `gerais-de-jogo.md`, antes do commit.
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

CODEX_DESCRIPTION_MAX = 1024
# Skill que também sai como .md solto no destino, com o nome que o documento de origem tinha.
LOOSE_MARKDOWN = {"code-audit": "code-audit-skill.md"}
BACKUP_SUFFIX = ".antigo"
# Lições de jogo que valem em qualquer engine: uma fonte na raiz e uma cópia igual em cada skill
# de motor. A lista é explícita: skill de motor nova entra acrescentando o nome aqui.
GENERAL_LESSONS_SOURCE = "gerais-de-jogo.md"
GENERAL_LESSONS_COPY = "references/gerais-de-jogo.md"
GENERAL_LESSONS_SKILLS = ("ai-first-defold", "ai-first-godot", "ai-first-lua")


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
    """Cópia das Gerais ausente ou diferente da fonte; fonte e cópias lidas no ref, não na árvore."""
    source = ref_blob(repo, ref, GENERAL_LESSONS_SOURCE)
    if source is None:
        return [f"{GENERAL_LESSONS_SOURCE} não existe no {ref}: é a fonte das cópias de "
                f"{', '.join(GENERAL_LESSONS_SKILLS)}"]
    problems = []
    for skill in GENERAL_LESSONS_SKILLS:
        path = f"{skill}/{GENERAL_LESSONS_COPY}"
        copy = ref_blob(repo, ref, path)
        if copy == source:
            continue
        why = "não existe" if copy is None else f"difere a partir da linha {first_differing_line(source, copy)}"
        problems.append(f"{path} no {ref} {why}; a fonte é {GENERAL_LESSONS_SOURCE}: regrave com "
                        f"`distribuir.py --repo <worktree> --copiar-gerais` e faça commit")
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
    for problem in problems:
        print(f"PROBLEMA: {problem}")
    print(note)
    if problems:
        print(f"{len(problems)} problema(s).")
        return 1
    print("tudo em dia.")
    return 0


# --- geração -----------------------------------------------------------------------------------

def remove_entry(path):
    """Apaga um .antigo gerado por este script: arquivo, link ou pasta (sem seguir link)."""
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def install(new_path, final):
    """Põe new_path em final; o que havia em final vira final.antigo."""
    backup = final + BACKUP_SUFFIX
    if os.path.lexists(final):
        remove_entry(backup)
        os.rename(final, backup)
        print(f"escrito: {final} (o anterior ficou em {backup})")
    else:
        print(f"escrito: {final}")
    os.rename(new_path, final)


def generate_zip(args, skill, tree, workdir):
    final = os.path.join(args.destino, f"{skill}.zip")
    if compare_zip(final, tree) is None:
        print(f"igual: {final}")
        return
    new_path = os.path.join(workdir, f"{skill}.zip")
    content = git(args.repo, "archive", "--format=zip", f"--prefix={skill}/", f"{args.ref}:{skill}").stdout
    with open(new_path, "wb") as handle:
        handle.write(content)
    install(new_path, final)


def generate_folder(args, skill, tree, workdir):
    final = os.path.join(args.destino, f"{skill}.skill")
    if compare_folder(final, tree) is None:
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
    install(new_path, final)


def generate_markdown(args, skill, tree, workdir):
    name = LOOSE_MARKDOWN[skill]
    final, content = os.path.join(args.destino, name), tree[f"{skill}/SKILL.md"][0]
    if compare_file(final, content) is None:
        print(f"igual: {final}")
        return
    new_path = os.path.join(workdir, name)
    with open(new_path, "wb") as handle:
        handle.write(content)
    install(new_path, final)


def run_generate(args, skills):
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


# --- cópias das Gerais de jogo -----------------------------------------------------------------

def general_lessons_source(args):
    """Conteúdo da fonte das Gerais na árvore de trabalho; sai com erro antes de escrever qualquer
    cópia se o checkout está no ref, se a fonte falta ou se falta a pasta de alguma skill."""
    branch = git(args.repo, "symbolic-ref", "-q", "--short", "HEAD", check=False).stdout.decode().strip()
    if branch == args.ref:
        # A pasta que toda sessão carrega fica no main e sem mudança local (README).
        sys.exit(f"erro: --copiar-gerais escreve na árvore de trabalho de {args.repo}, que está no "
                 f"{args.ref}; a lição entra numa worktree em ramo próprio: passe --repo <worktree>")
    source = os.path.join(args.repo, GENERAL_LESSONS_SOURCE)
    if not os.path.isfile(source):
        sys.exit(f"erro: a fonte {source} não existe; esperado {GENERAL_LESSONS_SOURCE} na raiz de --repo")
    missing = [s for s in GENERAL_LESSONS_SKILLS if not os.path.isdir(os.path.join(args.repo, s))]
    if missing:
        sys.exit(f"erro: sem a pasta da skill {', '.join(missing)} em {args.repo}; esperado uma pasta "
                 f"para cada nome de GENERAL_LESSONS_SKILLS ({', '.join(GENERAL_LESSONS_SKILLS)})")
    with open(source, "rb") as handle:
        return handle.read()


def run_copy_general(args):
    """Regrava, na árvore de trabalho de --repo, as cópias das Gerais a partir da fonte dela."""
    content = general_lessons_source(args)
    written = 0
    for skill in GENERAL_LESSONS_SKILLS:
        target = os.path.join(args.repo, skill, GENERAL_LESSONS_COPY)
        if compare_file(target, content) is None:
            print(f"igual: {target}")
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(content)
        print(f"escrito: {target}")
        written += 1
    if written:
        print("nota: só a árvore de trabalho mudou; o --check confere o commit")
    return 0


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
    parser.add_argument("--ref", default="main", help="ref que é a fonte (padrão: main)")
    parser.add_argument("--destino", default="~/Documentos/Skills", help="pasta dos zips e cópias")
    parser.add_argument("--links", default="~/.agents/skills", help="pasta dos symlinks do Codex")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="só confere; sai com 1 se houver problema")
    mode.add_argument("--copiar-gerais", action="store_true",
                      help=f"só regrava <skill>/{GENERAL_LESSONS_COPY} a partir do "
                           f"{GENERAL_LESSONS_SOURCE} da árvore de trabalho de --repo")
    args = parser.parse_args(argv)
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
    refuse_destination(args.repo, args.destino)
    skills = list_skills(args.repo, args.ref)
    if not skills:
        sys.exit(f"erro: nenhuma pasta com SKILL.md no {args.ref} de {args.repo}")
    print(f"fonte: {args.repo} @ {args.ref} ({git_text(args.repo, 'rev-parse', '--short', args.ref)}); "
          f"skills: {', '.join(skills)}")
    return run_check(args, skills) if args.check else run_generate(args, skills)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
