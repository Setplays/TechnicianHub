import webview
import os
import base64
import json
import sys

# --- CLASSE DE API (A PONTE ENTRE O SITE E O PYTHON) ---
class Api:
    def _get_folder(self):
        # Define o caminho: Documentos/TechnicianHub
        home_dir = os.path.expanduser("~")
        docs_dir = os.path.join(home_dir, "Documents")
        target_folder = os.path.join(docs_dir, "TechnicianHub")
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        return target_folder

    def salvar_pdf_no_disco(self, base64_data, filename):
        try:
            folder = self._get_folder()
            
            # Limpa o cabeçalho do Base64 se vier do JS
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]

            file_path = os.path.join(folder, filename)
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(base64_data))
            
            return {"status": "success", "path": file_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def salvar_dados(self, dados_json):
        """Salva as configurações e preenchimentos em um arquivo JSON"""
        try:
            folder = self._get_folder()
            file_path = os.path.join(folder, "settings.json")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(dados_json)
            return "ok"
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            return "error"

    def carregar_dados(self):
        """Lê o arquivo JSON e devolve para o Javascript"""
        try:
            folder = self._get_folder()
            file_path = os.path.join(folder, "settings.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            return "{}" # Retorna JSON vazio se não existir arquivo
        except Exception as e:
            print(f"Erro ao ler configurações: {e}")
            return "{}"

# --- CÓDIGO HTML/JS ---
HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechnicianHub | Setplays</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        :root {
            --primary-os: #2c3e50;
            --primary-orc: #27ae60;
            --primary-rec: #195e38;
            --bg-color: #f0f2f5;
            --card-bg: #ffffff;
            --text-color: #333333;
            --text-secondary: #555555;
            --input-bg: #ffffff;
            --input-border: #cccccc;
            --settings-bg: #f8f9fa;
            --header-bg: #333333;
            --brand-color: #e74c3c;
        }
        body.dark-mode {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #e0e0e0;
            --text-secondary: #bbbbbb;
            --input-bg: #2d2d2d;
            --input-border: #444444;
            --settings-bg: #252525;
            --header-bg: #000000;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            transition: background-color 0.3s, color 0.3s;
            user-select: none;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: var(--card-bg);
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            min-height: 85vh;
            transition: background-color 0.3s;
        }
        .header {
            background-color: var(--header-bg);
            color: white;
            padding: 15px 20px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            letter-spacing: 1px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            -webkit-app-region: drag;
        }
        .header-title { flex-grow: 1; text-align: center; }
        .header-actions { display: flex; gap: 15px; -webkit-app-region: no-drag; }
        .icon-btn { background: none; border: none; color: #aaa; cursor: pointer; font-size: 1.2rem; transition: color 0.2s; }
        .icon-btn:hover { color: #fff; }
        .tabs { display: flex; cursor: pointer; border-bottom: 1px solid var(--input-border); }
        .tab {
            flex: 1; padding: 15px; text-align: center; background-color: var(--settings-bg);
            font-weight: bold; transition: all 0.3s ease; color: var(--text-secondary);
            border-bottom: 4px solid transparent;
        }
        .tab:hover { background-color: var(--input-border); }
        .tab.active-os { background-color: var(--primary-os); color: white; border-bottom-color: var(--primary-os); }
        .tab.active-orc { background-color: var(--primary-orc); color: white; border-bottom-color: var(--primary-orc); }
        .tab.active-rec { background-color: var(--primary-rec); color: white; border-bottom-color: var(--primary-rec); }
        .tab-content { display: none; padding: 20px; animation: fadeIn 0.4s; flex-grow: 1; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .form-group { margin-bottom: 15px; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; color: var(--text-color); }
        input, textarea, select {
            width: 100%; padding: 10px; 
            border: 1px solid var(--input-border); 
            background-color: var(--input-bg);
            color: var(--text-color);
            border-radius: 5px;
            box-sizing: border-box; font-family: inherit;
            transition: border-color 0.3s, background-color 0.3s, color 0.3s;
        }
        input:focus, textarea:focus { outline: none; border-color: var(--primary-os); }
        .btn {
            width: 100%; padding: 12px; border: none; border-radius: 5px;
            color: white; font-size: 1rem; font-weight: bold; cursor: pointer;
            margin-top: 10px; transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.9; }
        .btn-os { background-color: var(--primary-os); }
        .btn-orc { background-color: var(--primary-orc); }
        .btn-rec { background-color: var(--primary-rec); }
        .settings-area {
            margin-top: 20px; padding: 20px; 
            background-color: var(--settings-bg); 
            border-top: 1px solid var(--input-border);
            transition: background-color 0.3s;
        }
        .color-picker-group { display: flex; gap: 15px; margin-bottom: 15px; }
        .color-item { flex: 1; display: flex; flex-direction: column; align-items: center; }
        .color-item input[type="color"] { height: 40px; cursor: pointer; padding: 0; border: none; background: none; }
        .template-selector { display: flex; gap: 10px; margin-bottom: 15px; }
        .template-card {
            flex: 1; padding: 10px; border: 2px solid var(--input-border); border-radius: 8px;
            text-align: center; cursor: pointer; transition: 0.2s; color: var(--text-color);
        }
        .template-card:hover { border-color: #999; }
        .template-card.selected { border-color: var(--primary-os); background-color: var(--input-bg); font-weight: bold; }
        .checkbox-wrapper { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; color: var(--text-color); }
        .checkbox-wrapper input { width: auto; }
        .signature-preview {
            max-width: 150px; max-height: 80px; border: 1px dashed var(--input-border); margin-top: 10px; display: block;
            background-image: linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%);
            background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        }
        .app-footer { background-color: #111; color: #888; text-align: center; padding: 15px; font-size: 0.8rem; margin-top: auto; }
        .brand-link { text-decoration: none; color: inherit; transition: opacity 0.3s; }
        .brand-link:hover { opacity: 0.8; }
        .brand-mark { font-weight: 800; color: #fff; font-family: 'Verdana', sans-serif; letter-spacing: 1px; text-transform: uppercase; }
        .brand-dot { color: var(--brand-color); }
        @media (max-width: 600px) { .row, .color-picker-group { flex-direction: column; gap: 10px; } }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <div style="width:60px"></div> <div class="header-title">TechnicianHub</div>
        <div class="header-actions">
            <button class="icon-btn" id="theme-toggle" onclick="toggleDarkMode()" title="Alternar Modo Escuro">🌙</button>
            <button class="icon-btn" onclick="scrollToConfig()" title="Configurações">⚙️</button>
        </div>
    </div>

    <div class="tabs">
        <div class="tab active-os" onclick="openTab('os', this)">ORDEM DE SERVIÇO</div>
        <div class="tab" onclick="openTab('orcamento', this)">ORÇAMENTO</div>
        <div class="tab" onclick="openTab('recibo', this)">RECIBO</div>
    </div>

    <div id="os" class="tab-content active">
        <h3 style="color: var(--primary-os)">Dados da Ordem de Serviço</h3>
        <div class="form-group"><label>Nome do Cliente:</label><input type="text" id="os_nome" oninput="saveData()"></div>
        <div class="row">
            <div class="col form-group"><label>CPF:</label><input type="text" id="os_cpf" maxlength="14" onkeyup="maskCPF(this)" oninput="saveData()"></div>
            <div class="col form-group"><label>Telefone:</label><input type="text" id="os_tel" maxlength="15" onkeyup="maskPhone(this)" oninput="saveData()"></div>
        </div>
        <div class="form-group"><label>Endereço:</label><input type="text" id="os_end" oninput="saveData()"></div>
        <hr style="border-color: var(--input-border);">
        <div class="form-group"><label>Equipamento:</label><input type="text" id="os_equip" oninput="saveData()"></div>
        <div class="form-group"><label>Defeito:</label><input type="text" id="os_defeito" oninput="saveData()"></div>
        <div class="form-group"><label>Parecer Técnico:</label><textarea id="os_parecer" rows="3" oninput="saveData()"></textarea></div>
        <div class="checkbox-wrapper"><label for="os_check_garantia">Imprimir Termos?</label><input type="checkbox" id="os_check_garantia" checked onchange="saveData()"></div>
        <div class="form-group"><label>Termos:</label><textarea id="os_garantia" rows="3" oninput="saveData()">90 dias para serviços e 30 dias para peças.</textarea></div>
        <div class="row">
            <div class="col form-group"><label>Produtos (R$):</label><input type="text" id="os_val_prod" onkeyup="maskMoney(this)" oninput="saveData()"></div>
            <div class="col form-group"><label>Serviços (R$):</label><input type="text" id="os_val_serv" onkeyup="maskMoney(this)" oninput="saveData()"></div>
        </div>
        <button class="btn btn-os" onclick="generatePDF('OS')">EMITIR O.S. (PDF)</button>
    </div>

    <div id="orcamento" class="tab-content">
        <h3 style="color: var(--primary-orc)">Dados do Orçamento</h3>
        <div class="form-group"><label>Nome do Cliente:</label><input type="text" id="orc_nome" oninput="saveData()"></div>
        <div class="row">
            <div class="col form-group"><label>CPF:</label><input type="text" id="orc_cpf" maxlength="14" onkeyup="maskCPF(this)" oninput="saveData()"></div>
            <div class="col form-group"><label>Telefone:</label><input type="text" id="orc_tel" maxlength="15" onkeyup="maskPhone(this)" oninput="saveData()"></div>
        </div>
        <div class="form-group"><label>Endereço:</label><input type="text" id="orc_end" oninput="saveData()"></div>
        <hr style="border-color: var(--input-border);">
        <div class="form-group"><label>Equipamento:</label><input type="text" id="orc_equip" oninput="saveData()"></div>
        <div class="form-group"><label>Problema:</label><input type="text" id="orc_problema" oninput="saveData()"></div>
        <div class="form-group"><label>Serviços Propostos:</label><textarea id="orc_desc" rows="4" oninput="saveData()"></textarea></div>
        <div class="form-group"><label>Validade:</label><input type="text" id="orc_validade" value="15 dias" oninput="saveData()"></div>
        <div class="row">
            <div class="col form-group"><label>Visita (R$):</label><input type="text" id="orc_val_visita" onkeyup="maskMoney(this)" oninput="saveData()"></div>
            <div class="col form-group"><label>Serviços (R$):</label><input type="text" id="orc_val_servicos" onkeyup="maskMoney(this)" oninput="saveData()"></div>
        </div>
        <button class="btn btn-orc" onclick="generatePDF('ORC')">EMITIR ORÇAMENTO (PDF)</button>
    </div>

    <div id="recibo" class="tab-content">
        <h3 style="color: var(--primary-rec)">Dados do Recibo</h3>
        <div class="form-group"><label>Data:</label><input type="text" id="rec_data" onkeyup="maskDate(this)" oninput="saveData()"></div>
        <div class="form-group"><label>Pagador:</label><input type="text" id="rec_nome" oninput="saveData()"></div>
        <div class="form-group"><label>Documento:</label>
            <div class="checkbox-wrapper"><input type="radio" name="doc_type" value="CNPJ" checked onchange="toggleDocType()"> CNPJ <input type="radio" name="doc_type" value="CPF" onchange="toggleDocType()"> CPF</div>
            <input type="text" id="rec_doc_num" maxlength="18" placeholder="Número" onkeyup="maskDocRecibo(this)" oninput="saveData()">
        </div>
        <hr style="border-color: var(--input-border);">
        <div class="form-group"><label>Valor (R$):</label><input type="text" id="rec_valor" onkeyup="maskMoney(this)" oninput="saveData()"></div>
        <div class="form-group"><label>Referente a:</label><textarea id="rec_desc" rows="4" oninput="saveData()"></textarea></div>
        <button class="btn btn-rec" onclick="generatePDF('REC')">EMITIR RECIBO (PDF)</button>
    </div>

    <div class="settings-area" id="config-area">
        <h4 style="color: var(--text-color)">Customização</h4>
        
        <div style="background-color: var(--input-bg); padding: 15px; border: 1px solid var(--input-border); border-radius: 5px; margin-bottom: 20px;">
            <h5 style="margin-top:0; color: var(--primary-os)">Dados do Profissional (Cabeçalho)</h5>
            <div class="form-group"><label>Nome/Empresa:</label><input type="text" id="cfg_tech_nome" placeholder="Ex: João Silva Tech" oninput="saveData()"></div>
            <div class="form-group"><label>Cargo/Título:</label><input type="text" id="cfg_tech_cargo" placeholder="Ex: Técnico em Informática" oninput="saveData()"></div>
            
            <div class="row">
                <div class="col form-group"><label>CPF/CNPJ:</label><input type="text" id="cfg_tech_doc" maxlength="18" placeholder="000.000.000-00" onkeyup="maskDocGeneric(this)" oninput="saveData()"></div>
                <div class="col form-group"><label>Telefone/Contato:</label><input type="text" id="cfg_tech_tel" maxlength="15" placeholder="(99) 99999-9999" onkeyup="maskPhone(this)" oninput="saveData()"></div>
            </div>
            
            <div class="row">
                <div class="col form-group"><label>Endereço (Linha 1):</label><input type="text" id="cfg_tech_end1" placeholder="Ex: Rua das Flores, 123" oninput="saveData()"></div>
                <div class="col form-group"><label>Endereço (Linha 2):</label><input type="text" id="cfg_tech_end2" placeholder="Ex: Centro - RJ" oninput="saveData()"></div>
            </div>
        </div>

        <label>Escolha as Cores do Sistema/PDF:</label>
        <div class="color-picker-group">
            <div class="color-item"><label style="font-size:0.8rem">O.S.</label><input type="color" id="cfg_color_os" value="#2c3e50" oninput="updateTheme(true)"></div>
            <div class="color-item"><label style="font-size:0.8rem">Orçamento</label><input type="color" id="cfg_color_orc" value="#27ae60" oninput="updateTheme(true)"></div>
            <div class="color-item"><label style="font-size:0.8rem">Recibo</label><input type="color" id="cfg_color_rec" value="#195e38" oninput="updateTheme(true)"></div>
        </div>
        <button style="width:auto; padding:5px 10px; margin-bottom:15px; font-size:0.8rem; background:#666;" class="btn" onclick="resetTheme()">Restaurar Cores Padrão</button>

        <label>Modelo do PDF:</label>
        <div class="template-selector">
            <div class="template-card selected" id="tpl_classic" onclick="selectTemplate('classic')">Clássico</div>
            <div class="template-card" id="tpl_minimal" onclick="selectTemplate('minimal')">Minimalista</div>
            <div class="template-card" id="tpl_modern" onclick="selectTemplate('modern')">Executivo</div>
        </div>
        <input type="hidden" id="selected_template" value="classic">

        <hr style="margin:20px 0; border-color: var(--input-border);">
        
        <label>Assinatura Digital:</label>
        <input type="file" id="signature_file" accept="image/*" onchange="uploadSignature(this)">
        <img id="sig_preview" class="signature-preview" style="display:none;">
        <button style="background:#888; width:auto; padding:5px 10px; font-size:0.8rem;" class="btn" onclick="clearSignature()">Remover Assinatura</button>
    </div>

    <div class="app-footer">
        Developed by <a href="https://github.com/Setplays" target="_blank" class="brand-link"><span class="brand-mark">SETPLAYS<span class="brand-dot">.</span></span></a>
    </div>
</div>

<script>
    function toggleDarkMode() {
        const body = document.body;
        body.classList.toggle('dark-mode');
        document.getElementById('theme-toggle').innerText = body.classList.contains('dark-mode') ? '☀️' : '🌙';
        saveData();
    }
    function openTab(tabName, clickedTab) {
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active-os', 'active-orc', 'active-rec'));
        document.getElementById(tabName).classList.add('active');
        if(tabName === 'os') clickedTab.classList.add('active-os');
        if(tabName === 'orcamento') clickedTab.classList.add('active-orc');
        if(tabName === 'recibo') clickedTab.classList.add('active-rec');
    }
    function scrollToConfig() { document.getElementById('config-area').scrollIntoView({ behavior: 'smooth' }); }

    function updateTheme(save = false) {
        const os = document.getElementById('cfg_color_os').value;
        const orc = document.getElementById('cfg_color_orc').value;
        const rec = document.getElementById('cfg_color_rec').value;
        document.documentElement.style.setProperty('--primary-os', os);
        document.documentElement.style.setProperty('--primary-orc', orc);
        document.documentElement.style.setProperty('--primary-rec', rec);
        if(save) saveData();
    }
    function resetTheme() {
        document.getElementById('cfg_color_os').value = "#2c3e50";
        document.getElementById('cfg_color_orc').value = "#27ae60";
        document.getElementById('cfg_color_rec').value = "#195e38";
        updateTheme(true);
    }
    function selectTemplate(tpl) {
        document.getElementById('selected_template').value = tpl;
        document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
        document.getElementById('tpl_' + tpl).classList.add('selected');
        saveData();
    }

    function maskCPF(i) { i.value = i.value.replace(/\D/g,"").replace(/(\d{3})(\d)/,"$1.$2").replace(/(\d{3})(\d)/,"$1.$2").replace(/(\d{3})(\d{1,2})$/,"$1-$2"); }
    function maskPhone(i) { i.value = i.value.replace(/\D/g,"").replace(/^(\d{2})(\d)/g,"($1) $2").replace(/(\d)(\d{4})$/,"$1-$2"); }
    function maskMoney(i) { 
        let v = i.value.replace(/\D/g,""); v = (v/100).toFixed(2) + ""; 
        i.value = v.replace(".", ",").replace(/(\d)(\d{3})(\d{3}),/g, "$1.$2.$3,").replace(/(\d)(\d{3}),/g, "$1.$2,"); 
    }
    function maskDate(i) { i.value = i.value.replace(/\D/g,"").replace(/(\d{2})(\d)/,"$1/$2").replace(/(\d{2})(\d)/,"$1/$2").substring(0, 10); }
    function maskDocGeneric(i) {
        let v = i.value.replace(/\D/g,"");
        if (v.length > 14) v = v.substring(0, 14);
        if (v.length <= 11) {
            i.value = v.replace(/(\d{3})(\d)/,"$1.$2").replace(/(\d{3})(\d)/,"$1.$2").replace(/(\d{3})(\d{1,2})$/,"$1-$2");
        } else {
            i.value = v.replace(/^(\d{2})(\d)/,"$1.$2").replace(/^(\d{2})\.(\d{3})(\d)/,"$1.$2.$3").replace(/\.(\d{3})(\d)/,".$1/$2").replace(/(\d{4})(\d)/,"$1-$2");
        }
    }
    function maskDocRecibo(i) { 
        if(document.querySelector('input[name="doc_type"]:checked').value === 'CPF') maskCPF(i); 
        else { let v=i.value.replace(/\D/g,""); i.value = v.replace(/^(\d{2})(\d)/,"$1.$2").replace(/^(\d{2})\.(\d{3})(\d)/,"$1.$2.$3").replace(/\.(\d{3})(\d)/,".$1/$2").replace(/(\d{4})(\d)/,"$1-$2"); }
    }
    function toggleDocType() { document.getElementById('rec_doc_num').value = ''; saveData(); }

    // --- NOVA LÓGICA DE SALVAMENTO COM PERSISTÊNCIA NO DISCO ---
    function saveData() {
        const data = {};
        document.querySelectorAll('input, textarea').forEach(el => {
            if (el.type === 'checkbox' || el.type === 'radio') {
                if (el.checked) data[el.id || el.name] = el.value;
                if (el.type === 'checkbox') data[el.id] = el.checked;
            } else if (el.type !== 'file') data[el.id] = el.value;
        });
        data.darkMode = document.body.classList.contains('dark-mode');
        
        // Salva no LocalStorage (Backup Rápido)
        localStorage.setItem('technicianHubData', JSON.stringify(data));

        // Salva no Disco via Python (Backup Definitivo)
        // Verifica se a API do Python já está disponível
        if(window.pywebview && window.pywebview.api) {
            window.pywebview.api.salvar_dados(JSON.stringify(data));
        }
    }

    async function loadData() {
        document.getElementById('rec_data').value = new Date().toLocaleDateString('pt-BR');
        
        let saved = null;

        // Tenta carregar do Python (Prioridade Máxima)
        if(window.pywebview && window.pywebview.api) {
            try {
                saved = await window.pywebview.api.carregar_dados();
            } catch(e) { console.log("Erro ao carregar do disco"); }
        }

        // Se falhar ou vier vazio, tenta do LocalStorage (Fallback)
        if (!saved || saved === "{}") {
            saved = localStorage.getItem('technicianHubData');
        }

        if (saved) {
            const data = JSON.parse(saved);
            if (data.darkMode) {
                document.body.classList.add('dark-mode');
                document.getElementById('theme-toggle').innerText = '☀️';
            }
            for (const key in data) {
                const el = document.getElementById(key);
                if (el) {
                    if (el.type === 'checkbox') el.checked = data[key];
                    else el.value = data[key];
                    if(key.includes('cfg_color')) updateTheme(false); 
                } else {
                    document.getElementsByName(key).forEach(r => { if (r.value === data[key]) r.checked = true; });
                }
            }
            if(data['selected_template']) selectTemplate(data['selected_template']);
        }
        const savedSig = localStorage.getItem('technicianHubSignature');
        if(savedSig) { document.getElementById('sig_preview').src = savedSig; document.getElementById('sig_preview').style.display = 'block'; }
    }

    function uploadSignature(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = (e) => processImageBackground(e.target.result);
            reader.readAsDataURL(input.files[0]);
        }
    }
    function processImageBackground(base64Image) {
        const img = new Image(); img.src = base64Image;
        img.onload = function() {
            const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
            const ctx = c.getContext('2d'); ctx.drawImage(img, 0, 0);
            const d = ctx.getImageData(0, 0, c.width, c.height);
            for (let i=0; i<d.data.length; i+=4) if(d.data[i]>210 && d.data[i+1]>210 && d.data[i+2]>210) d.data[i+3]=0;
            ctx.putImageData(d, 0, 0);
            const res = c.toDataURL('image/png');
            localStorage.setItem('technicianHubSignature', res);
            document.getElementById('sig_preview').src = res; document.getElementById('sig_preview').style.display = 'block';
        }
    }
    function clearSignature() {
        localStorage.removeItem('technicianHubSignature');
        document.getElementById('sig_preview').style.display = 'none';
        document.getElementById('signature_file').value = '';
    }

    async function generatePDF(type) {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({ unit: 'mm', format: 'a4' });
        
        const colors = {
            OS: document.getElementById('cfg_color_os').value,
            ORC: document.getElementById('cfg_color_orc').value,
            REC: document.getElementById('cfg_color_rec').value
        };
        const primaryColor = colors[type];
        const tpl = document.getElementById('selected_template').value;

        const tecnico = {
            nome: document.getElementById('cfg_tech_nome').value.toUpperCase() || "NOME DO TÉCNICO",
            cargo: document.getElementById('cfg_tech_cargo').value.toUpperCase() || "TÉCNICO ESPECIALIZADO",
            cpf: document.getElementById('cfg_tech_doc').value || "",
            tel: document.getElementById('cfg_tech_tel').value || "",
            end1: document.getElementById('cfg_tech_end1').value || "Endereço Linha 1",
            end2: document.getElementById('cfg_tech_end2').value || "Endereço Linha 2"
        };
        const sigData = localStorage.getItem('technicianHubSignature');

        if(type === 'REC') {
            drawReceipt(doc, primaryColor, sigData, tecnico);
            drawSignatures(doc, type, sigData, tecnico);
        } else {
            const data = gatherData(type);
            if(tpl === 'minimal') drawMinimal(doc, primaryColor, tecnico, data, type);
            else if(tpl === 'modern') drawModern(doc, primaryColor, tecnico, data, type);
            else drawClassic(doc, primaryColor, tecnico, data, type);
            
            drawSignatures(doc, type, sigData, tecnico);
        }

        const filename = `${type}_${tpl}_Setplays_${new Date().getTime()}.pdf`;
        const pdfBase64 = doc.output('datauristring'); 

        window.pywebview.api.salvar_pdf_no_disco(pdfBase64, filename).then(response => {
            if (response.status === 'success') {
                alert("Emissão bem sucedida!\n\nO arquivo foi salvo em:\n" + response.path);
            } else {
                alert("Erro ao salvar: " + response.message);
            }
        });
    }

    function gatherData(type) {
        const prefix = type === 'OS' ? 'os' : 'orc';
        return {
            nome: document.getElementById(prefix+'_nome').value,
            cpf: document.getElementById(prefix+'_cpf').value,
            tel: document.getElementById(prefix+'_tel').value,
            end: document.getElementById(prefix+'_end').value,
            equip: document.getElementById(prefix+'_equip').value,
            label1: type === 'OS' ? "Defeito Apresentado:" : "Problema Relatado:",
            val1: type === 'OS' ? document.getElementById('os_defeito').value : document.getElementById('orc_problema').value,
            label2: type === 'OS' ? "Parecer Técnico:" : "Serviços Propostos:",
            val2: type === 'OS' ? document.getElementById('os_parecer').value : document.getElementById('orc_desc').value,
            termos: (type === 'OS' && !document.getElementById('os_check_garantia').checked) ? "" : (type === 'OS' ? document.getElementById('os_garantia').value : `Validade: ${document.getElementById('orc_validade').value}`),
            v1: type === 'OS' ? document.getElementById('os_val_prod').value : document.getElementById('orc_val_visita').value,
            v2: type === 'OS' ? document.getElementById('os_val_serv').value : document.getElementById('orc_val_servicos').value,
            l1: type === 'OS' ? "Produtos" : "Visita",
            l2: type === 'OS' ? "Serviços" : "Mão de Obra"
        };
    }

    function drawClassic(doc, color, tec, data, type) {
        doc.setFillColor(color); doc.rect(0, 0, 210, 40, 'F');
        doc.setTextColor(255); doc.setFont("helvetica", "bold"); doc.setFontSize(22); doc.text(tec.nome, 10, 15);
        doc.setFont("helvetica", "normal"); doc.setFontSize(12); doc.text(tec.cargo, 10, 22);
        doc.setFontSize(9); 
        doc.text(tec.cpf + (tec.cpf && tec.tel ? " | " : "") + tec.tel, 200, 15, {align:'right'});
        doc.text(tec.end1, 200, 20, {align:'right'}); 
        doc.text(tec.end2, 200, 25, {align:'right'}); 
        doc.text(`Emissão: ${new Date().toLocaleDateString('pt-BR')}`, 200, 35, {align:'right'});
        doc.setFillColor(255); doc.roundedRect(10, 28, 90, 15, 2, 2, 'F');
        doc.setTextColor(color); doc.setFontSize(16); doc.setFont("helvetica", "bold");
        doc.text(type === 'OS' ? "ORDEM DE SERVIÇO" : "ORÇAMENTO", 15, 38);
        let y = 55;
        doc.setFillColor('#f3f4f6'); doc.rect(10, y, 190, 8, 'F');
        doc.setTextColor(color); doc.setFontSize(10); doc.text("DADOS DO CLIENTE", 12, y+5);
        y += 15;
        doc.setTextColor(0);
        doc.setFont("helvetica", "bold"); doc.text("Nome:", 12, y); doc.setFont("helvetica", "normal"); doc.text(data.nome, 25, y);
        doc.setFont("helvetica", "bold"); doc.text("Documento:", 120, y); doc.setFont("helvetica", "normal"); doc.text(data.cpf, 145, y);
        y += 7;
        doc.setFont("helvetica", "bold"); doc.text("Endereço:", 12, y); doc.setFont("helvetica", "normal"); doc.text(data.end, 32, y);
        doc.setFont("helvetica", "bold"); doc.text("Telefone:", 120, y); doc.setFont("helvetica", "normal"); doc.text(data.tel, 145, y);
        y += 15;
        doc.setFillColor('#f3f4f6'); doc.rect(10, y, 190, 8, 'F');
        doc.setTextColor(color); doc.setFont("helvetica", "bold"); doc.text("DETALHES", 12, y+5);
        y += 15;
        doc.setTextColor(0);
        doc.setFont("helvetica", "bold"); doc.text("Equipamento:", 12, y); 
        y += 5;
        doc.setFont("helvetica", "normal"); doc.text(data.equip, 12, y);
        y += 8;
        doc.setFont("helvetica", "bold"); doc.text(data.label1, 12, y); doc.setFont("helvetica", "normal"); doc.text(data.val1, 12, y+5);
        y += 15;
        doc.setFont("helvetica", "bold"); doc.text(data.label2, 12, y); y += 5;
        doc.setFont("helvetica", "normal");
        const lines = doc.splitTextToSize(data.val2, 180);
        doc.text(lines, 12, y);
        y += (lines.length * 5) + 10;
        doc.setDrawColor(200); doc.setFillColor(252, 252, 252); doc.roundedRect(10, y, 190, 35, 2, 2, 'FD');
        y += 10;
        doc.text(`${data.l1}:`, 20, y); doc.text(`R$ ${data.v1}`, 190, y, {align:'right'}); y += 7;
        doc.text(`${data.l2}:`, 20, y); doc.text(`R$ ${data.v2}`, 190, y, {align:'right'}); y += 5;
        doc.line(20, y, 190, y); y += 8;
        const tot = (parseFloat(data.v1.replace(',','.')) + parseFloat(data.v2.replace(',','.'))).toFixed(2).replace('.',',');
        doc.setTextColor(color); doc.setFontSize(12); doc.setFont("helvetica", "bold");
        doc.text("TOTAL", 20, y); doc.text(`R$ ${tot}`, 190, y, {align:'right'});
        if(data.termos) { y += 20; doc.setTextColor(100); doc.setFontSize(8); doc.text(data.termos, 10, y); }
    }

    function drawMinimal(doc, color, tec, data, type) {
        doc.setTextColor(color); doc.setFont("helvetica", "bold"); doc.setFontSize(26);
        doc.text(type === 'OS' ? "ORDEM DE SERVIÇO" : "ORÇAMENTO", 10, 20);
        doc.setTextColor(100); doc.setFontSize(10); doc.setFont("helvetica", "bold");
        doc.text(tec.nome.toUpperCase(), 10, 30);
        doc.setFont("helvetica", "normal"); 
        doc.text(`${tec.cpf} | ${tec.tel}`, 10, 35); 
        doc.text(tec.end2, 10, 40);
        doc.text(`Data: ${new Date().toLocaleDateString('pt-BR')}`, 10, 45);
        doc.setDrawColor(color); doc.setLineWidth(0.5); doc.line(10, 50, 200, 50);
        let y = 60;
        doc.setTextColor(color); doc.setFont("helvetica", "bold"); doc.setFontSize(12); doc.text("CLIENTE", 10, y); y += 7;
        doc.setTextColor(0); doc.setFont("helvetica", "normal"); doc.setFontSize(10);
        doc.text(`Nome: ${data.nome}`, 10, y); doc.text(`Documento: ${data.cpf}`, 120, y); y += 6;
        doc.text(`Endereço: ${data.end}`, 10, y); doc.text(`Telefone: ${data.tel}`, 120, y); y += 15;
        doc.setTextColor(color); doc.setFont("helvetica", "bold"); doc.setFontSize(12); doc.text("SERVIÇO", 10, y); y += 7;
        doc.setTextColor(0); doc.setFont("helvetica", "bold"); doc.setFontSize(10);
        doc.text("Equipamento:", 10, y); 
        doc.setFont("helvetica", "normal"); doc.text(data.equip, 40, y); y += 7;
        doc.setFont("helvetica", "bold"); doc.text(data.label1, 10, y);
        doc.setFont("helvetica", "normal"); doc.text(data.val1, 10, y+5); y += 12;
        doc.setFont("helvetica", "bold"); doc.text(data.label2, 10, y); y+=5;
        const lines = doc.splitTextToSize(data.val2, 190); doc.text(lines, 10, y); y += (lines.length * 5) + 15;
        doc.line(10, y, 200, y); y += 10;
        doc.text(`${data.l1}: R$ ${data.v1}`, 10, y); doc.text(`${data.l2}: R$ ${data.v2}`, 80, y);
        const tot = (parseFloat(data.v1.replace(',','.')) + parseFloat(data.v2.replace(',','.'))).toFixed(2).replace('.',',');
        doc.setFont("helvetica", "bold"); doc.setTextColor(color); doc.setFontSize(14); doc.text(`TOTAL: R$ ${tot}`, 150, y);
        if(data.termos) { y += 20; doc.setFontSize(8); doc.setTextColor(150); doc.text(data.termos, 10, y); }
    }

    function drawModern(doc, color, tec, data, type) {
        doc.setFillColor(color); doc.rect(0, 0, 210, 50, 'F');
        doc.setTextColor(255); doc.setFont("helvetica", "bold"); doc.setFontSize(24);
        const title = type === 'OS' ? "ORDEM DE SERVIÇO" : "ORÇAMENTO";
        doc.text(title, 15, 25);
        doc.setFontSize(10); doc.text(tec.nome, 200, 18, {align: 'right'});
        doc.setFont("helvetica", "normal"); doc.setFontSize(9); doc.text(tec.cargo, 200, 24, {align: 'right'});
        doc.text(`${tec.cpf} | ${tec.tel}`, 200, 30, {align: 'right'});
        doc.text(tec.end2, 200, 36, {align: 'right'});
        doc.text(`Emissão: ${new Date().toLocaleDateString('pt-BR')}`, 200, 42, {align: 'right'});
        let y = 65;
        doc.setFillColor(247, 247, 247); doc.roundedRect(15, y, 180, 28, 2, 2, 'F');
        doc.setFillColor(color); doc.rect(15, y, 3, 28, 'F'); 
        doc.setTextColor(color); doc.setFont("helvetica", "bold"); doc.setFontSize(9); doc.text("CLIENTE", 22, y+8);
        doc.setTextColor(0); doc.setFontSize(11); doc.text(data.nome.toUpperCase(), 20, y+18);
        doc.setFont("helvetica", "normal"); doc.setFontSize(9); 
        doc.text(`Documento: ${data.cpf}`, 120, y+8);
        doc.text(`Telefone: ${data.tel}`, 120, y+13);
        doc.text(`Endereço: ${data.end}`, 120, y+18);
        y += 40;
        doc.setTextColor(color); doc.setFont("helvetica", "bold"); doc.text("DESCRIÇÃO DOS SERVIÇOS", 15, y);
        doc.setDrawColor(200); doc.line(15, y+2, 195, y+2); y += 10;
        doc.setTextColor(0); doc.setFont("helvetica", "bold"); doc.text("Equipamento:", 15, y);
        doc.setFont("helvetica", "normal"); doc.text(data.equip, 45, y); y += 8;
        doc.setFont("helvetica", "bold"); doc.text(data.label1, 15, y);
        doc.setFont("helvetica", "normal"); doc.text(data.val1, 15, y+5); y += 12;
        doc.setFont("helvetica", "bold"); doc.text(data.label2, 15, y); y += 5;
        const lines = doc.splitTextToSize(data.val2, 180);
        doc.text(lines, 15, y); y += (lines.length * 5) + 15;
        y += 5;
        doc.setFillColor(color); doc.roundedRect(120, y, 75, 24, 2, 2, 'F');
        const tot = (parseFloat(data.v1.replace(',','.')) + parseFloat(data.v2.replace(',','.'))).toFixed(2).replace('.',',');
        doc.setTextColor(255); doc.setFontSize(8); doc.text("VALOR TOTAL", 185, y+7, {align:'right'});
        doc.setFontSize(16); doc.setFont("helvetica", "bold"); doc.text(`R$ ${tot}`, 185, y+17, {align:'right'});
        doc.setTextColor(0); doc.setFontSize(9); doc.setFont("helvetica", "normal");
        doc.text(`${data.l1}: R$ ${data.v1}`, 115, y+8, {align:'right'});
        doc.text(`${data.l2}: R$ ${data.v2}`, 115, y+16, {align:'right'});
        if(data.termos) { y += 35; doc.setFontSize(7); doc.setTextColor(150); doc.text(data.termos, 15, y); }
    }

    function drawReceipt(doc, color, sigData, tec) {
        const nome = document.getElementById('rec_nome').value;
        const docType = document.querySelector('input[name="doc_type"]:checked').value;
        const docNum = document.getElementById('rec_doc_num').value;
        const valor = document.getElementById('rec_valor').value;
        const desc = document.getElementById('rec_desc').value;
        const dataRaw = document.getElementById('rec_data').value;
        doc.setTextColor(color); doc.setFontSize(18); doc.setFont("helvetica", "bold");
        doc.text("RECIBO DE SERVIÇO", 105, 40, { align: 'center' });
        doc.setFontSize(10); doc.setTextColor(100);
        doc.text(tec.nome, 105, 20, { align: 'center' });
        doc.setFontSize(8);
        doc.text(`${tec.cpf} | ${tec.tel}`, 105, 25, { align: 'center' });
        doc.setTextColor(0); doc.setFontSize(14); doc.setFont("helvetica", "normal");
        const txt = `Recebi de ${nome} (${docType}: ${docNum}) a quantia de R$${valor} referente a: ${desc}.`;
        doc.text(doc.splitTextToSize(txt, 160), 25, 70);
        doc.text(`Rio de Janeiro, ${dataRaw}`, 105, 130, {align:'center'});
    }

    function drawSignatures(doc, type, sigData, tec) {
        let y = type === 'REC' ? 160 : 260;
        doc.setDrawColor(0); doc.setTextColor(0); doc.setFontSize(10);
        if (type !== 'REC') {
            doc.line(20, y, 90, y); doc.text("Cliente", 55, y+5, {align:'center'});
            doc.line(120, y, 190, y); doc.text(tec.nome, 155, y+5, {align:'center'});
            if(sigData) doc.addImage(sigData, 'PNG', 140, y-25, 30, 25);
        } else {
            doc.line(70, y, 140, y); doc.text(tec.nome, 105, y+5, {align:'center'});
            if(sigData) doc.addImage(sigData, 'PNG', 90, y-25, 30, 25);
        }
    }

    // GARANTE QUE CARREGA APENAS DEPOIS DO PYTHON ESTAR PRONTO
    window.addEventListener('pywebviewready', loadData);
</script>
</body>
</html>
r"""

def run_app():
    # Inicializa a API
    api = Api()

    # Cria um arquivo temporário HTML para carregar no webview
    html_file = os.path.join(os.getcwd(), "sistema_tecnico.html")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    
    # Cria a janela da aplicação e passa a 'api' para o JS usar
    window = webview.create_window(
        "TechnicianHub - Sistema de Gestão", 
        url=html_file,
        width=1000, 
        height=850,
        resizable=True,
        js_api=api 
    )
    
    webview.start()

if __name__ == '__main__':
    run_app()