#!/usr/bin/env python3
"""Tracker de contatos com recrutadores (SQLite, sem dependências externas)."""
import argparse
import os
import shutil
import sqlite3
import sys
import zipfile
from datetime import datetime, timedelta

DB_PATH = os.environ.get(
    "JOB_OUTREACH_DB",
    os.path.join(os.path.expanduser("~"), ".linkedin-job-outreach", "tracker.db"),
)
PROFILE_PATH = os.environ.get(
    "JOB_OUTREACH_PROFILE",
    os.path.join(os.path.expanduser("~"), ".linkedin-job-outreach", "profile.md"),
)
REFERENCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
TEMPLATE_PATH = os.path.join(REFERENCES_DIR, "profile.template.md")
APPLICATION_PATH = os.environ.get(
    "JOB_OUTREACH_APPLICATION",
    os.path.join(os.path.expanduser("~"), ".linkedin-job-outreach", "candidatura.md"),
)
APPLICATION_TEMPLATE = os.path.join(REFERENCES_DIR, "candidatura.template.md")
TEMPLATE_MARKER = "<!-- TEMPLATE"
CV_DIR = os.environ.get(
    "JOB_OUTREACH_CV_DIR",
    os.path.join(os.path.expanduser("~"), ".linkedin-job-outreach", "cv"),
)
CV_MEMORY = os.path.join(CV_DIR, "memoria.md")
CV_EXTS = (".pdf", ".docx", ".md", ".txt")
STATUSES = ("sent", "replied", "interview", "rejected", "ghosted")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            role TEXT,
            url TEXT,
            channel TEXT,
            score INTEGER,
            status TEXT NOT NULL DEFAULT 'sent',
            notes TEXT,
            contacted_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    return con


def now():
    return datetime.now().isoformat(timespec="seconds")


def fmt(row):
    return (
        f"#{row['id']} | {row['contacted_at'][:10]} | {row['status']:<9} | "
        f"{row['name']} @ {row['company'] or '-'} | {row['role'] or '-'} | "
        f"nota {row['score'] if row['score'] is not None else '-'} | {row['channel'] or '-'}"
        + (f" | {row['notes']}" if row["notes"] else "")
    )


def cmd_add(a, con):
    ts = now()
    cur = con.execute(
        "INSERT INTO contacts (name, company, role, url, channel, score, status, notes, contacted_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 'sent', ?, ?, ?)",
        (a.name, a.company, a.role, a.url, a.channel, a.score, a.notes, ts, ts),
    )
    con.commit()
    print(f"Registrado #{cur.lastrowid}: {a.name} @ {a.company or '-'}")


def cmd_check(a, con):
    clauses, params = [], []
    if a.name:
        clauses.append("LOWER(name) = LOWER(?)")
        params.append(a.name.strip())
    if a.url:
        clauses.append("url = ?")
        params.append(a.url.strip())
    if not clauses:
        sys.exit("Informe --name ou --url")
    rows = con.execute(
        f"SELECT * FROM contacts WHERE {' OR '.join(clauses)} ORDER BY contacted_at DESC", params
    ).fetchall()
    if a.company:
        company_rows = con.execute(
            "SELECT * FROM contacts WHERE LOWER(company) = LOWER(?) ORDER BY contacted_at DESC",
            (a.company.strip(),),
        ).fetchall()
    else:
        company_rows = []
    if not rows and not company_rows:
        print("NOVO: nenhum contato anterior")
        return
    limit = (datetime.now() - timedelta(days=a.days)).isoformat()
    if rows:
        recent = [r for r in rows if r["contacted_at"] >= limit]
        print(f"JA_CONTATADO_RECENTE (≤{a.days}d)" if recent else "CONTATADO_ANTES")
    else:
        print("RECRUTADOR_NOVO_EMPRESA_JA_CONTATADA (avalie se vale abordar outra pessoa da mesma empresa)")
    for r in rows:
        print("  recrutador: " + fmt(r))
    others = [r for r in company_rows if r["id"] not in {x["id"] for x in rows}]
    for r in others:
        print("  mesma empresa: " + fmt(r))


def cmd_list(a, con):
    q, params = "SELECT * FROM contacts WHERE 1=1", []
    if a.status:
        q += " AND status = ?"
        params.append(a.status)
    if a.older_than is not None:
        q += " AND updated_at <= ?"
        params.append((datetime.now() - timedelta(days=a.older_than)).isoformat())
    q += " ORDER BY contacted_at DESC"
    rows = con.execute(q, params).fetchall()
    if not rows:
        print("Nenhum registro")
    for r in rows:
        print(fmt(r))


def cmd_update(a, con):
    row = con.execute("SELECT * FROM contacts WHERE id = ?", (a.id,)).fetchone()
    if not row:
        sys.exit(f"ID {a.id} não encontrado")
    notes = row["notes"]
    if a.notes:
        notes = f"{notes} / {a.notes}" if notes else a.notes
    con.execute(
        "UPDATE contacts SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
        (a.status, notes, now(), a.id),
    )
    con.commit()
    print(f"#{a.id} -> {a.status}")


def cmd_stats(a, con):
    total = con.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    print(f"Total de contatos: {total}")
    for s in STATUSES:
        n = con.execute("SELECT COUNT(*) FROM contacts WHERE status = ?", (s,)).fetchone()[0]
        pct = f" ({n / total:.0%})" if total else ""
        print(f"  {s:<9} {n}{pct}")


def cmd_today(a, con):
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    n = con.execute("SELECT COUNT(*) FROM contacts WHERE contacted_at >= ?", (start,)).fetchone()[0]
    print(f"Enviados hoje: {n}/{a.limit} (restam {max(a.limit - n, 0)})")


def ensure_from_template(path, template):
    # Arquivos pessoais ficam fora da pasta da skill para sobreviver a atualizações do plugin
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copyfile(template, path)
        print(f"CRIADO: {path}")
        return
    with open(path, encoding="utf-8") as f:
        status = "INCOMPLETO" if TEMPLATE_MARKER in f.read() else "OK"
    print(f"{status}: {path}")


def cmd_profile(a, con):
    ensure_from_template(PROFILE_PATH, TEMPLATE_PATH)


def cmd_application(a, con):
    ensure_from_template(APPLICATION_PATH, APPLICATION_TEMPLATE)


def stored_cv():
    if not os.path.isdir(CV_DIR):
        return None
    for ext in CV_EXTS:
        path = os.path.join(CV_DIR, "cv" + ext)
        if os.path.exists(path):
            return path
    return None


def docx_text(path):
    # DOCX é um zip com XML; extrai parágrafos sem depender de python-docx
    import re
    from xml.etree import ElementTree

    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    lines = []
    for par in root.iter(ns + "p"):
        text = "".join(t.text or "" for t in par.iter(ns + "t"))
        lines.append(text)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def cmd_cv(a, con):
    # CV fica fora da pasta da skill: atualizações do plugin apagam essa pasta
    if a.import_path:
        src = os.path.expanduser(a.import_path.strip().strip('"'))
        ext = os.path.splitext(src)[1].lower()
        if not os.path.isfile(src):
            sys.exit(f"ERRO: arquivo não encontrado: {src}")
        if ext not in CV_EXTS:
            sys.exit(f"ERRO: formato {ext or '(sem extensão)'} não suportado; use {', '.join(CV_EXTS)}")
        os.makedirs(CV_DIR, exist_ok=True)
        dest = os.path.join(CV_DIR, "cv" + ext)
        old = stored_cv()
        if old and os.path.exists(dest) and os.path.samefile(src, dest):
            print(f"JA_IMPORTADO: {dest}")
        else:
            if old:
                os.remove(old)
            shutil.copyfile(src, dest)
            print(f"IMPORTADO: {dest}")
    cv = stored_cv()
    if not cv:
        print("SEM_CV")
        return
    if not a.import_path:
        mtime = datetime.fromtimestamp(os.path.getmtime(cv)).isoformat(timespec="seconds")
        print(f"CV: {cv} (copiado em {mtime})")
    print(f"MEMORIA: {CV_MEMORY} ({'existe' if os.path.exists(CV_MEMORY) else 'ausente'})")
    if a.text:
        ext = os.path.splitext(cv)[1]
        if ext == ".pdf":
            print(f"PDF: leia o arquivo diretamente: {cv}")
        elif ext == ".docx":
            print("--- TEXTO ---")
            print(docx_text(cv))
        else:
            print("--- TEXTO ---")
            with open(cv, encoding="utf-8", errors="replace") as f:
                print(f.read())


def main():
    # Windows usa cp1252 no stdout redirecionado; "≤" e nomes acentuados quebrariam o print
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add")
    s.add_argument("--name", required=True)
    s.add_argument("--company")
    s.add_argument("--role")
    s.add_argument("--url")
    s.add_argument("--channel", choices=["dm", "comment", "invite", "email", "form"])
    s.add_argument("--score", type=int)
    s.add_argument("--notes")

    s = sub.add_parser("check")
    s.add_argument("--name")
    s.add_argument("--company")
    s.add_argument("--url")
    s.add_argument("--days", type=int, default=30)

    s = sub.add_parser("list")
    s.add_argument("--status", choices=STATUSES)
    s.add_argument("--older-than", type=int, dest="older_than")

    s = sub.add_parser("update")
    s.add_argument("--id", type=int, required=True)
    s.add_argument("--status", choices=STATUSES, required=True)
    s.add_argument("--notes")

    sub.add_parser("stats")

    s = sub.add_parser("today")
    s.add_argument("--limit", type=int, default=10)

    sub.add_parser("profile")
    sub.add_parser("candidatura")

    s = sub.add_parser("cv")
    s.add_argument("--import", dest="import_path", help="copia este arquivo como o CV atual")
    s.add_argument("--text", action="store_true", help="imprime o texto do CV (DOCX/MD/TXT)")

    a = p.parse_args()
    con = connect()
    {
        "add": cmd_add,
        "check": cmd_check,
        "list": cmd_list,
        "update": cmd_update,
        "stats": cmd_stats,
        "today": cmd_today,
        "profile": cmd_profile,
        "candidatura": cmd_application,
        "cv": cmd_cv,
    }[a.cmd](a, con)


if __name__ == "__main__":
    main()
