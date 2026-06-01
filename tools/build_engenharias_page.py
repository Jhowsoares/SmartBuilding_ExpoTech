"""Atualiza cronograma web + JSON a partir do Excel (.xlsb).

Uso (após editar o cronograma):
    python tools/build_engenharias_page.py

Requisito: pip install pyxlsb
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
XLSB_PATH = ROOT / "docs" / "engenharias" / "entregaveis" / "cronograma-projeto-faculdade.xlsb"
JSON_PATH = ROOT / "docs" / "engenharias" / "cronograma-data.json"
OUT_PATH = ROOT / "docs" / "engenharias.html"
PDF_DIR = "engenharias/entregaveis/em_pdf"

PDF_ENTREGAVEIS = [
    ("Projeto integrador - Eng. Civil.pdf", "Eng. Civil", "Relatório integrador", "./civil.html"),
    ("Projeto integrador.pdf", "Eng. Civil", "Vista 3D do laboratório", "./civil.html#modelo-3d"),
    (
        "Relatório Finaceiro de Implementação de Projeto.pdf",
        "Eng. Produção",
        "Relatório financeiro",
        "./producao.html",
    ),
    ("Arquitetura do sistema.pdf", "Eng. Computação", "Arquitetura do sistema", "./computacao.html"),
    (
        "Relatorio_de_Escopo_e_Arquitetura_Funcional.pdf",
        "Eng. Computação",
        "Escopo e arquitetura funcional",
        None,
    ),
]


def load_cronogram_from_xlsb() -> dict:
    from pyxlsb import open_workbook

    if not XLSB_PATH.exists():
        raise FileNotFoundError(f"Cronograma não encontrado: {XLSB_PATH}")

    out: dict = {}
    with open_workbook(XLSB_PATH) as wb:
        for name in wb.sheets:
            tasks: list = []
            with wb.get_sheet(name) as sh:
                for i, row in enumerate(sh.rows()):
                    if i < 7:
                        continue
                    cells = [c.v for c in row]
                    if len(cells) > 2 and isinstance(cells[0], (int, float)) and cells[1]:
                        desc = str(cells[2] if len(cells) > 2 else "").replace("\n", " | ")
                        if desc.strip() and desc != "None":
                            tasks.append({"id": int(cells[0]), "desc": desc.strip()})
                    elif (
                        len(cells) > 0
                        and isinstance(cells[0], str)
                        and ("DEV" in str(cells[0]) or "Eng" in str(cells[0]))
                    ):
                        tasks.append({"section": str(cells[0])})
            out[name] = tasks
    return out


def render_table(data: dict, sheet_name: str) -> str:
    rows: list[str] = []
    for item in data.get(sheet_name, []):
        if "section" in item:
            sec = item["section"].replace("&", "&amp;").replace("<", "&lt;")
            rows.append(
                f'<tr class="section-row"><td colspan="2"><strong>{sec}</strong></td></tr>'
            )
        else:
            desc = item["desc"].replace("&", "&amp;").replace("<", "&lt;")
            rows.append(f'<tr><td>{item["id"]}</td><td>{desc}</td></tr>')
    return "\n".join(rows)


def pdf_href(filename: str) -> str:
    return f"./{PDF_DIR}/{quote(filename)}"


def resolve_pdf_filename(filename: str) -> str:
    path = ROOT / "docs" / PDF_DIR / filename
    if path.exists():
        return filename
    folder = ROOT / "docs" / PDF_DIR
    match = next((p.name for p in folder.glob("*.pdf") if p.name.lower() == filename.lower()), None)
    if match:
        return match
    match = next(
        (p.name for p in folder.glob("*.pdf") if filename.split(".")[0][:20] in p.name),
        filename,
    )
    return match if match else filename


def build_pdf_rows() -> str:
    rows = []
    for filename, area, desc, page in PDF_ENTREGAVEIS:
        filename = resolve_pdf_filename(filename)
        href = pdf_href(filename)
        links = f'<a href="{href}" style="color:#4d8eff">Baixar PDF</a>'
        if page:
            links += f' · <a href="{page}" style="color:#4d8eff">Página</a>'
        rows.append(f"<tr><td>{desc}</td><td>{area}</td><td>{links}</td></tr>")
    rows.append(
        f'<tr><td>Cronograma integrado</td><td>Todas</td>'
        f'<td><a href="./engenharias/entregaveis/cronograma-projeto-faculdade.xlsb" style="color:#4d8eff">Baixar Excel (.xlsb)</a></td></tr>'
    )
    return "\n".join(rows)


def main() -> None:
    data = load_cronogram_from_xlsb()
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    cron_tabs = ""
    for key, sheet, label in [
        ("civil", "Cronograma Civil", "Eng. Civil"),
        ("comp", "Cronograma Computação", "Eng. Computação"),
        ("elec", "Cronograma Elétrica", "Eng. Elétrica"),
    ]:
        body = render_table(data, sheet)
        display = "block" if key == "civil" else "none"
        cron_tabs += f"""
    <div id="tab-{key}" class="cron-tab" style="display:{display}">
      <h3 style="margin-bottom:12px;color:#adc6ff">{label}</h3>
      <div class="table-wrap">
        <table><thead><tr><th>#</th><th>Tarefa</th></tr></thead><tbody>
        {body}
        </tbody></table>
      </div>
    </div>"""

    pdf_rows = build_pdf_rows()
    civil_pdf = pdf_href(resolve_pdf_filename("Projeto integrador - Eng. Civil.pdf"))
    producao_pdf = pdf_href(
        resolve_pdf_filename("Relatório Finaceiro de Implementação de Projeto.pdf")
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Projeto Integrador — Smart Building</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="./assets/site.css" />
  <style>
    .tabs{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
    .tab-btn{{background:var(--card);border:1px solid var(--border);color:var(--muted);padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px}}
    .tab-btn.active{{background:var(--btn);color:#fff;border-color:var(--btn)}}
    .sub{{color:var(--muted);font-size:13px;margin-bottom:20px}}
    .card-links{{display:flex;flex-wrap:wrap;gap:8px 12px;margin-top:auto}}
    .card-links a{{color:var(--btn);font-size:13px;text-decoration:none;font-weight:500}}
    tr.section-row td{{background:rgba(77,142,255,.08);color:var(--accent)}}
  </style>
</head>
<body>
  <nav class="site-nav">
    <div class="container inner">
      <a class="site-brand" href="./index.html">
        <img src="./assets/logo-mark.svg" alt="" width="32" height="32" />
        Smart Building · Integrador
      </a>
      <div class="site-links">
        <a href="./index.html">Apresentação</a>
        <a href="./sistema.html">Arquitetura</a>
        <a href="./api.html" class="nav-cta">API (ReDoc)</a>
        <a href="https://github.com/Jhowsoares/SmartBuilding_ExpoTech">GitHub</a>
      </div>
    </div>
  </nav>

  <div class="eng-subnav">
    <div class="container inner">
      <a href="./engenharias.html" class="active">Panorama</a>
      <a href="./civil.html">Civil</a>
      <a href="./eletrica.html">Elétrica</a>
      <a href="./producao.html">Produção</a>
      <a href="./computacao.html">Computação</a>
    </div>
  </div>

  <div class="hero container">
    <span class="pill">ExpoTech 2026 · UniFECAF</span>
    <h1>Projeto Integrador Multidisciplinar</h1>
    <p>Automação inteligente de climatização no laboratório de elétrica (subsolo). Quatro engenharias — Civil, Elétrica, Produção e Computação — em um único ecossistema.</p>
  </div>

  <section class="container" id="engenharias">
    <h2 class="section-title">As quatro engenharias</h2>
    <p class="section-sub">Resumo integrado e entregáveis oficiais em PDF.</p>
    <div class="grid">
      <article class="card">
        <div class="card-head">
          <div class="icon-box green"><svg viewBox="0 0 24 24"><path d="M3 21h18M5 21V9l7-4 7 4v12"/></svg></div>
          <h3>Eng. Civil</h3>
        </div>
        <p>Infraestrutura, conforto térmico, maquete e modelo 3D.</p>
        <div class="card-links">
          <a href="./civil.html">Página Civil →</a>
          <a href="./civil.html#modelo-3d">Vista 3D →</a>
          <a href="{civil_pdf}">PDF →</a>
        </div>
      </article>
      <article class="card">
        <div class="card-head">
          <div class="icon-box amber"><svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
          <h3>Eng. Elétrica</h3>
        </div>
        <p>Arduino, sensores, Bluetooth, integração MQTT.</p>
        <div class="card-links"><a href="./eletrica.html">Página Elétrica →</a></div>
      </article>
      <article class="card">
        <div class="card-head">
          <div class="icon-box green"><svg viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg></div>
          <h3>Eng. Produção</h3>
        </div>
        <p>CAPEX, OPEX, ROI e cronograma integrado.</p>
        <div class="card-links">
          <a href="./producao.html">Página Produção →</a>
          <a href="{producao_pdf}">PDF →</a>
        </div>
      </article>
      <article class="card">
        <div class="card-head">
          <div class="icon-box"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg></div>
          <h3>Eng. Computação</h3>
        </div>
        <p>API REST, MQTT, ML, dashboard React.</p>
        <div class="card-links">
          <a href="./computacao.html">Página Computação →</a>
          <a href="./sistema.html">Arquitetura →</a>
        </div>
      </article>
    </div>
  </section>

  <section class="container" id="cronograma">
    <h2 class="section-title">Cronograma integrado</h2>
    <p class="section-sub">Visualização web (atualizada a partir do Excel). Use o botão para baixar o arquivo original.</p>
    <a class="btn" href="./engenharias/entregaveis/cronograma-projeto-faculdade.xlsb">Baixar cronograma (.xlsb)</a>
    <div class="tabs" style="margin-top:24px">
      <button class="tab-btn active" data-tab="civil">Civil</button>
      <button class="tab-btn" data-tab="comp">Computação</button>
      <button class="tab-btn" data-tab="elec">Elétrica</button>
    </div>
    {cron_tabs}
  </section>

  <section class="container" id="entregaveis">
    <h2 class="section-title">Entregáveis oficiais (PDF)</h2>
    <p class="section-sub">Documentos formais por engenharia. Após editar o Excel, rode <code style="color:#adc6ff">python tools/build_engenharias_page.py</code>.</p>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Documento</th><th>Área</th><th>Download</th></tr></thead>
        <tbody>
        {pdf_rows}
        </tbody>
      </table>
    </div>
  </section>

  <section class="container" id="equipe">
    <h2 class="section-title">Equipe integradora</h2>
    <p class="section-sub"><a href="./index.html" style="color:#4d8eff">Voltar à apresentação</a></p>
    <div class="grid">
      <div class="card"><h3>Computação</h3><p>Jhonata, João, Rickelmy, Felipe, Claudio</p></div>
      <div class="card"><h3>Civil</h3><p>Kayke, Nicolas, Renan, Lucca, Bruno</p></div>
      <div class="card"><h3>Produção</h3><p>Pedro Henrique, Samuel</p></div>
      <div class="card"><h3>Elétrica</h3><p>Equipe a confirmar no entregável formal</p></div>
    </div>
  </section>

  <footer class="site-footer">
    <p>Smart Building · ExpoTech 2026</p>
    <p style="margin-top:8px"><a href="./index.html">Apresentação</a> · <a href="./documentacao.html">Mapa docs</a> · <a href="./sistema.html">Arquitetura</a></p>
  </footer>

  <script>
    document.querySelectorAll('.tab-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.cron-tab').forEach(t => t.style.display = 'none');
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).style.display = 'block';
      }});
    }});
  </script>
</body>
</html>
"""

    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"OK: {JSON_PATH.relative_to(ROOT)}")
    print(f"OK: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
