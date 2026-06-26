"""CSS del dashboard."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}
.main{background:#F4F5F7}
.block-container{padding:1rem 1.5rem!important;max-width:100%!important}
section[data-testid="stSidebar"]{background:#1A2540!important;min-width:220px!important;max-width:220px!important}
section[data-testid="stSidebar"] *{color:#C8D0E0!important}
section[data-testid="stSidebar"] p{color:#7B8FAE!important;font-size:10px!important;
    text-transform:uppercase;letter-spacing:.08em;font-weight:500;margin-bottom:4px}
.kpi{background:#fff;border-radius:8px;padding:.9rem 1.1rem;
    border-left:3px solid #1A2540;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:4px}
.kpi.bad{border-left-color:#C5372C}.kpi.good{border-left-color:#2D7A4F}
.kpi-lbl{font-size:10px;font-weight:500;color:#7B8FAE;text-transform:uppercase;
    letter-spacing:.08em;margin-bottom:5px}
.kpi-val{font-size:20px;font-weight:500;color:#1A2540;line-height:1.1}
.kpi-val.bad{color:#C5372C}.kpi-val.good{color:#2D7A4F}
.kpi-note{font-size:11px;color:#7B8FAE;margin-top:3px}
.card{background:#fff;border-radius:8px;padding:.9rem 1.1rem;
    border:0.5px solid #E2E5EC;box-shadow:0 1px 3px rgba(0,0,0,.04);margin-bottom:.6rem}
.card-title{font-size:10px;font-weight:500;color:#7B8FAE;text-transform:uppercase;
    letter-spacing:.08em;margin-bottom:8px;padding-bottom:6px;border-bottom:0.5px solid #F0F1F4}
.frow{display:flex;align-items:center;justify-content:space-between;
    padding:5px 0;border-bottom:0.5px solid #F4F5F7;cursor:pointer}
.frow:last-child{border-bottom:none}
.frow:hover{background:#F8F9FA;margin:0 -4px;padding:5px 4px;border-radius:4px}
.fn{font-size:12px;font-weight:500;color:#1A2540}
.fv{font-size:12px;font-weight:500}
.fs{font-size:10px;color:#7B8FAE}
.ib{display:inline-block;width:6px;height:6px;border-radius:50%;background:#C5372C;margin-right:6px}
.ig{display:inline-block;width:6px;height:6px;border-radius:50%;background:#2D7A4F;margin-right:6px}
.pill{display:inline-block;font-size:9px;padding:2px 6px;border-radius:3px;font-weight:500;margin-left:4px}
.pn{background:#FDF3DC;color:#7A5300}.pc{background:#E4EEF9;color:#14488A}
.po{background:#F5E8F5;color:#6A2080}.pa{background:#E3F2E8;color:#1B5C35}
.nav-bar{display:flex;align-items:center;gap:8px;margin-bottom:.8rem;
    padding-bottom:.6rem;border-bottom:0.5px solid #E2E5EC}
.nav-title{font-size:15px;font-weight:500;color:#1A2540;flex:1}
.nav-sub{font-size:11px;color:#7B8FAE}
.breadcrumb{font-size:11px;color:#7B8FAE;margin-bottom:.5rem}
.breadcrumb span{color:#1A2540;font-weight:500}
.stTabs [data-baseweb="tab-list"]{background:transparent;border-bottom:1.5px solid #E2E5EC;gap:0}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:0;padding:7px 18px;
    font-size:12px;font-weight:500;color:#7B8FAE;border-bottom:2px solid transparent;margin-bottom:-1.5px}
.stTabs [aria-selected="true"]{color:#1A2540!important;border-bottom:2px solid #1A2540!important;
    background:transparent!important}
</style>
"""
