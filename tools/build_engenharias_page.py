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

# PDFs oficiais para download (relativos a docs/)
PDF_ENTREGAVEIS = [
    ("Projeto integrador - Eng. Civil.pdf", "Eng. Civil", "Relatório integrador"),
    ("Relatório Finaceiro de Implementação de Projeto.pdf", "Eng. Produção", "Relatório financeiro"),
    ("Projeto integrador.pdf", "Conceito", "Visão geral do laboratório"),
    ("Arquitetura do sistema.pdf", "Eng. Computação", "Arquitetura do sistema"),
    ("Relatorio_de_Escopo_e_Arquitetura_Funcional.pdf", "Eng. Computação", "Escopo e arquitetura funcional"),
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


def build_pdf_rows() -> str:
    rows = []
    for filename, area, desc in PDF_ENTREGAVEIS:
        path = ROOT / "docs" / PDF_DIR / filename
        if not path.exists():
            # tenta match por nome similar (acentos)
            folder = ROOT / "docs" / PDF_DIR
            match = next((p.name for p in folder.glob("*.pdf") if p.name.lower() == filename.lower()), None)
            if match:
                filename = match
            else:
                match = next((p.name for p in folder.glob("*.pdf") if filename.split(".")[0][:20] in p.name), filename)
                filename = match if match else filename
        href = pdf_href(filename)
        rows.append(
            f'<tr><td>{desc}</td><td>{area}</td>'
            f'<td><a href="{href}" style="color:#4d8eff">Baixar PDF</a></td></tr>'
        )
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

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Projeto Integrador — Smart Building</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#0c1322;--card:#191f2f;--border:#424754;--muted:#8c909f;--text:#dce2f7;--accent:#adc6ff;--btn:#4d8eff}}
    body{{background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;line-height:1.6}}
    .container{{max-width:1000px;margin:0 auto;padding:0 20px}}
    nav{{position:sticky;top:0;z-index:50;background:rgba(12,19,34,.95);border-bottom:1px solid var(--border);padding:14px 0}}
    nav .inner{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
    nav a{{color:var(--muted);text-decoration:none;font-size:13px;margin-left:16px}}
    nav a:hover{{color:var(--text)}}
    nav .brand{{font-weight:700;color:var(--text)}}
    .hero{{text-align:center;padding:48px 20px 32px}}
    .hero h1{{font-size:clamp(22px,4vw,36px);margin-bottom:12px}}
    .hero p{{color:var(--muted);max-width:640px;margin:0 auto 24px}}
    .pill{{display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;background:rgba(173,198,255,.12);color:var(--accent);border:1px solid rgba(173,198,255,.25);margin:4px}}
    section{{padding:32px 0}}
    h2{{font-size:20px;margin-bottom:8px}}
    .sub{{color:var(--muted);font-size:13px;margin-bottom:20px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}}
    .card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px}}
    .card h3{{font-size:16px;margin-bottom:8px;color:var(--accent)}}
    .card p{{font-size:13px;color:var(--muted)}}
    .card a{{color:var(--btn);font-size:13px;text-decoration:none;margin-right:12px}}
    .flow{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;font-family:JetBrains Mono,monospace;font-size:12px;color:var(--muted);overflow-x:auto;white-space:pre;line-height:1.8}}
    .table-wrap{{overflow-x:auto;border:1px solid var(--border);border-radius:10px}}
    table{{width:100%;border-collapse:collapse;min-width:400px}}
    th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #2e3545;font-size:13px}}
    th{{background:#232a3a;color:var(--muted);font-size:11px;text-transform:uppercase}}
    tr.section-row td{{background:rgba(77,142,255,.08);color:var(--accent)}}
    .tabs{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
    .tab-btn{{background:var(--card);border:1px solid var(--border);color:var(--muted);padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px}}
    .tab-btn.active{{background:var(--btn);color:#fff;border-color:var(--btn)}}
    .btn{{display:inline-block;background:var(--btn);color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600;margin-top:12px}}
    .btn-outline{{background:transparent;border:1px solid var(--border);color:var(--text);margin-left:8px}}
    footer{{border-top:1px solid var(--border);padding:32px 20px;text-align:center;color:var(--muted);font-size:13px;margin-top:40px}}
    @media(max-width:640px){{nav a{{margin-left:0;margin-right:12px}}}}
  </style>
</head>
<body>
  <nav><div class="container inner">
    <span class="brand">Smart Building · Integrador</span>
    <div>
      <a href="./index.html">Apresentação</a>
      <a href="./sistema.html">Arquitetura</a>
      <a href="./civil.html">Eng. Civil</a>
      <a href="./api.html">API (ReDoc)</a>
      <a href="https://github.com/Jhowsoares/SmartBuilding_ExpoTech">GitHub</a>
    </div>
  </div></nav>

  <div class="hero container">
    <span class="pill">ExpoTech 2026 · UniFECAF</span>
    <h1>Projeto Integrador Multidisciplinar</h1>
    <p>Automação inteligente de climatização no laboratório de elétrica (subsolo). Quatro engenharias — Civil, Elétrica, Produção e Computação — em um único ecossistema.</p>
  </div>

  <section class="container" id="engenharias">
    <h2>As quatro engenharias</h2>
    <p class="sub">Resumo integrado e entregáveis oficiais em PDF.</p>
    <div class="grid">
      <div class="card">
        <h3>Eng. Civil</h3>
        <p>Infraestrutura, conforto térmico, maquete e modelo 3D.</p>
        <a href="./civil.html">Página Civil →</a>
        <a href="{pdf_href('Projeto integrador - Eng. Civil.pdf')}">PDF →</a>
      </div>
      <div class="card">
        <h3>Eng. Elétrica</h3>
        <p>Arduino, sensores, Bluetooth, integração MQTT.</p>
        <a href="{pdf_href('Projeto integrador.pdf')}">PDF conceito →</a>
      </div>
      <div class="card">
        <h3>Eng. Produção</h3>
        <p>CAPEX, OPEX, ROI e cronograma integrado.</p>
        <a href="{pdf_href('Relatório Finaceiro de Implementação de Projeto.pdf')}">PDF →</a>
      </div>
      <div class="card">
        <h3>Eng. Computação</h3>
        <p>API REST, MQTT, ML, dashboard React.</p>
        <a href="./sistema.html">Arquitetura →</a>
        <a href="{pdf_href('Arquitetura do sistema.pdf')}">PDF →</a>
      </div>
    </div>
  </section>

  <section class="container" id="cronograma">
    <h2>Cronograma integrado</h2>
    <p class="sub">Visualização web (atualizada a partir do Excel). Use o botão para baixar o arquivo original.</p>
    <a class="btn" href="./engenharias/entregaveis/cronograma-projeto-faculdade.xlsb">Baixar cronograma (.xlsb)</a>
    <div class="tabs" style="margin-top:24px">
      <button class="tab-btn active" data-tab="civil">Civil</button>
      <button class="tab-btn" data-tab="comp">Computação</button>
      <button class="tab-btn" data-tab="elec">Elétrica</button>
    </div>
    {cron_tabs}
  </section>

  <section class="container" id="entregaveis">
    <h2>Entregáveis oficiais (PDF)</h2>
    <p class="sub">Documentos formais para download. Após editar o Excel, rode <code style="color:#adc6ff">python tools/build_engenharias_page.py</code> para atualizar as abas abaixo.</p>
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
    <h2>Equipe integradora</h2>
    <p class="sub"><a href="./index.html" style="color:#4d8eff">Voltar à apresentação</a></p>
    <div class="grid">
      <div class="card"><h3>Computação</h3><p>Jhonata, João, Rickelmy, Felipe, Claudio</p></div>
      <div class="card"><h3>Civil</h3><p>Kayke, Nicolas, Renan, Lucca, Bruno</p></div>
      <div class="card"><h3>Produção</h3><p>Pedro Henrique, Samuel</p></div>
      <div class="card"><h3>Elétrica</h3><p>Equipe a confirmar no entregável formal</p></div>
    </div>
  </section>

  <footer>
    <p>Smart Building · ExpoTech 2026</p>
    <p style="margin-top:8px"><a href="./index.html" style="color:#4d8eff">Apresentação</a> · <a href="./sistema.html" style="color:#4d8eff">Arquitetura</a></p>
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
