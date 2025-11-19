import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime
import os
import sys
import json

# Mapeamento de meses
MESES = {
    1: 'JANEIRO', 2: 'FEVEREIRO', 3: 'MARÇO', 4: 'ABRIL',
    5: 'MAIO', 6: 'JUNHO', 7: 'JULHO', 8: 'AGOSTO',
    9: 'SETEMBRO', 10: 'OUTUBRO', 11: 'NOVEMBRO', 12: 'DEZEMBRO'
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SistemaTecnicoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Técnico - Salgatech")
        self.root.geometry("700x850")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- CARREGAMENTO DE RECURSOS ---
        try:
            icon_file = resource_path("icone.ico")
            self.root.iconbitmap(icon_file)
        except Exception as e:
            print(f"Ícone não encontrado: {e}")

        self.setup_directories()
        self.setup_menu()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", padding=[12, 5], font=('Arial', 10, 'bold'))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        self.tab_os = tk.Frame(self.notebook, bg="#f0f0f0")
        self.tab_orcamento = tk.Frame(self.notebook, bg="#f0f0f0")
        self.tab_recibo = tk.Frame(self.notebook, bg="#f0f0f0")

        self.notebook.add(self.tab_os, text="  ORDEM DE SERVIÇO  ")
        self.notebook.add(self.tab_orcamento, text="  ORÇAMENTO  ")
        self.notebook.add(self.tab_recibo, text="  RECIBO  ")

        self.setup_os_tab()
        self.setup_orcamento_tab()
        self.setup_recibo_tab()

        self.load_autosave()

    def setup_directories(self):
        try:
            user_docs = os.path.join(os.path.expanduser('~'), 'Documents')
            self.base_dir = os.path.join(user_docs, 'Salgatech')
            self.os_dir = os.path.join(self.base_dir, 'Servicos')
            self.orc_dir = os.path.join(self.base_dir, 'Orcamentos')
            self.rec_dir = os.path.join(self.base_dir, 'Recibos')
            self.data_dir = os.path.join(self.base_dir, 'DadosSalvos')

            os.makedirs(self.os_dir, exist_ok=True)
            os.makedirs(self.orc_dir, exist_ok=True)
            os.makedirs(self.rec_dir, exist_ok=True)
            os.makedirs(self.data_dir, exist_ok=True)
            
            self.autosave_file = os.path.join(self.data_dir, 'autosave.json')

        except Exception as e:
            messagebox.showerror("Erro de Pasta", f"Não foi possível criar as pastas: {e}")

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Abrir Arquivo...", command=self.load_file_dialog)
        filemenu.add_command(label="Salvar Arquivo Como...", command=self.save_file_dialog)
        filemenu.add_separator()
        filemenu.add_command(label="Limpar Tudo", command=self.clear_all_fields)
        filemenu.add_separator()
        filemenu.add_command(label="Sair", command=self.on_closing)
        menubar.add_cascade(label="Arquivo", menu=filemenu)
        self.root.config(menu=menubar)

    def create_field(self, parent, label_text, mask_type=None):
        lbl = tk.Label(parent, text=label_text, font=("Segoe UI", 9), bg="#ffffff")
        lbl.pack(anchor="w")
        entry = tk.Entry(parent, bd=1, relief="solid")
        entry.pack(fill="x", pady=(0, 5), ipady=3)
        
        if mask_type:
            entry.bind('<KeyRelease>', lambda event: self.format_entry(event, entry, mask_type))
        
        return entry

    def format_entry(self, event, entry, mask_type):
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'BackSpace', 'Delete'):
            return

        texto_atual = entry.get()
        apenas_numeros = ''.join(filter(str.isdigit, texto_atual))
        novo_texto = ""

        if mask_type == "doc_recibo":
            tipo = self.rec_tipo_doc.get()
            mask_type = "cpf" if tipo == "CPF" else "cnpj"

        if mask_type == "cpf":
            apenas_numeros = apenas_numeros[:11]
            if len(apenas_numeros) <= 3: novo_texto = apenas_numeros
            elif len(apenas_numeros) <= 6: novo_texto = f"{apenas_numeros[:3]}.{apenas_numeros[3:]}"
            elif len(apenas_numeros) <= 9: novo_texto = f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"
            else: novo_texto = f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"

        elif mask_type == "cnpj":
            apenas_numeros = apenas_numeros[:14]
            if len(apenas_numeros) <= 2: novo_texto = apenas_numeros
            elif len(apenas_numeros) <= 5: novo_texto = f"{apenas_numeros[:2]}.{apenas_numeros[2:]}"
            elif len(apenas_numeros) <= 8: novo_texto = f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:]}"
            elif len(apenas_numeros) <= 12: novo_texto = f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:8]}/{apenas_numeros[8:]}"
            else: novo_texto = f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:8]}/{apenas_numeros[8:12]}-{apenas_numeros[12:]}"

        elif mask_type == "tel":
            apenas_numeros = apenas_numeros[:11]
            if len(apenas_numeros) <= 2: novo_texto = f"({apenas_numeros}"
            elif len(apenas_numeros) <= 6: novo_texto = f"({apenas_numeros[:2]}) {apenas_numeros[2:]}"
            elif len(apenas_numeros) <= 10: novo_texto = f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
            else: novo_texto = f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
        
        elif mask_type == "data":
            apenas_numeros = apenas_numeros[:8]
            if len(apenas_numeros) <= 2: novo_texto = apenas_numeros
            elif len(apenas_numeros) <= 4: novo_texto = f"{apenas_numeros[:2]}/{apenas_numeros[2:]}"
            else: novo_texto = f"{apenas_numeros[:2]}/{apenas_numeros[2:4]}/{apenas_numeros[4:]}"
        else:
            novo_texto = texto_atual

        if novo_texto != texto_atual:
            entry.delete(0, tk.END)
            entry.insert(0, novo_texto)
            entry.icursor(tk.END)

    def get_all_data(self):
        return {
            'os_nome': self.os_nome.get(),
            'os_cpf': self.os_cpf.get(),
            'os_tel': self.os_tel.get(),
            'os_end': self.os_end.get(),
            'os_equip': self.os_equip.get(),
            'os_defeito': self.os_defeito.get(),
            'os_parecer': self.os_parecer.get("1.0", tk.END),
            'os_garantia': self.os_garantia.get("1.0", tk.END),
            'os_garantia_check': self.os_garantia_check_var.get(), # Novo campo
            'os_val_prod': self.os_val_prod.get(),
            'os_val_serv': self.os_val_serv.get(),
            'orc_nome': self.orc_nome.get(),
            'orc_cpf': self.orc_cpf.get(),
            'orc_tel': self.orc_tel.get(),
            'orc_end': self.orc_end.get(),
            'orc_equip': self.orc_equip.get(),
            'orc_problema': self.orc_problema.get(),
            'orc_desc': self.orc_desc.get("1.0", tk.END),
            'orc_validade': self.orc_validade.get(),
            'orc_val_visita': self.orc_val_visita.get(),
            'orc_val_servicos': self.orc_val_servicos.get(),
            'rec_data': self.rec_data.get(),
            'rec_nome': self.rec_nome.get(),
            'rec_tipo_doc': self.rec_tipo_doc.get(),
            'rec_doc_num': self.rec_doc_num.get(),
            'rec_valor': self.rec_valor.get(),
            'rec_desc': self.rec_desc.get("1.0", tk.END)
        }

    def set_all_data(self, data):
        if not data: return
        def set_entry(entry, value):
            entry.delete(0, tk.END)
            entry.insert(0, value if value else "")
        def set_text(text_widget, value):
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", value if value else "")

        set_entry(self.os_nome, data.get('os_nome', ''))
        set_entry(self.os_cpf, data.get('os_cpf', ''))
        set_entry(self.os_tel, data.get('os_tel', ''))
        set_entry(self.os_end, data.get('os_end', ''))
        set_entry(self.os_equip, data.get('os_equip', ''))
        set_entry(self.os_defeito, data.get('os_defeito', ''))
        set_text(self.os_parecer, data.get('os_parecer', ''))
        set_text(self.os_garantia, data.get('os_garantia', ''))
        self.os_garantia_check_var.set(data.get('os_garantia_check', True)) # Restaura o checkbox
        set_entry(self.os_val_prod, data.get('os_val_prod', ''))
        set_entry(self.os_val_serv, data.get('os_val_serv', ''))
        set_entry(self.orc_nome, data.get('orc_nome', ''))
        set_entry(self.orc_cpf, data.get('orc_cpf', ''))
        set_entry(self.orc_tel, data.get('orc_tel', ''))
        set_entry(self.orc_end, data.get('orc_end', ''))
        set_entry(self.orc_equip, data.get('orc_equip', ''))
        set_entry(self.orc_problema, data.get('orc_problema', ''))
        set_text(self.orc_desc, data.get('orc_desc', ''))
        set_entry(self.orc_validade, data.get('orc_validade', ''))
        set_entry(self.orc_val_visita, data.get('orc_val_visita', ''))
        set_entry(self.orc_val_servicos, data.get('orc_val_servicos', ''))
        set_entry(self.rec_data, data.get('rec_data', ''))
        set_entry(self.rec_nome, data.get('rec_nome', ''))
        self.rec_tipo_doc.set(data.get('rec_tipo_doc', 'CNPJ'))
        set_entry(self.rec_doc_num, data.get('rec_doc_num', ''))
        set_entry(self.rec_valor, data.get('rec_valor', ''))
        set_text(self.rec_desc, data.get('rec_desc', ''))

    def clear_all_fields(self):
        empty_data = {k: "" for k in self.get_all_data()}
        empty_data['rec_tipo_doc'] = "CNPJ"
        empty_data['rec_data'] = datetime.now().strftime("%d/%m/%Y")
        empty_data['orc_validade'] = "15 dias"
        empty_data['os_garantia'] = "90 dias para serviços e 30 dias para peças.\nGarantia cobre defeitos de fabricação ou serviço.\nObrigatório apresentar este documento."
        empty_data['os_garantia_check'] = True
        self.set_all_data(empty_data)

    def load_autosave(self):
        if os.path.exists(self.autosave_file):
            try:
                with open(self.autosave_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.set_all_data(data)
            except Exception as e:
                print(f"Erro ao carregar autosave: {e}")

    def on_closing(self):
        try:
            data = self.get_all_data()
            with open(self.autosave_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar autosave: {e}")
        self.root.destroy()

    def save_file_dialog(self):
        filepath = filedialog.asksaveasfilename(
            initialdir=self.data_dir,
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os Arquivos", "*.*")]
        )
        if filepath:
            try:
                data = self.get_all_data()
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar arquivo: {e}")

    def load_file_dialog(self):
        filepath = filedialog.askopenfilename(
            initialdir=self.data_dir,
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os Arquivos", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.set_all_data(data)
                messagebox.showinfo("Sucesso", "Dados carregados com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao abrir arquivo: {e}")

    # =========================================================================
    # TELA 1: ORDEM DE SERVIÇO
    # =========================================================================
    def setup_os_tab(self):
        frame = tk.Frame(self.tab_os, padx=20, pady=20, bg="#ffffff")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Dados da Ordem de Serviço", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#333").pack(anchor="w")

        self.os_nome = self.create_field(frame, "Nome do Cliente:")
        self.os_cpf = self.create_field(frame, "CPF (Somente Números):", mask_type="cpf") 
        self.os_tel = self.create_field(frame, "Telefone:", mask_type="tel")
        self.os_end = self.create_field(frame, "Endereço:")
        
        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=10)
        
        self.os_equip = self.create_field(frame, "Equipamento:")
        self.os_defeito = self.create_field(frame, "Defeito Apresentado:")
        
        tk.Label(frame, text="Parecer Técnico / Serviços Realizados:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5,0))
        self.os_parecer = tk.Text(frame, height=3, width=50, bd=1, relief="solid")
        self.os_parecer.pack(fill="x", pady=5)

        # --- MUDANÇA: Header com Checkbox para Garantia ---
        header_frame = tk.Frame(frame, bg="#ffffff")
        header_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(header_frame, text="Termos de Garantia:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(side="left")
        
        self.os_garantia_check_var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(header_frame, text="Imprimir no PDF", variable=self.os_garantia_check_var, 
                             bg="#ffffff", activebackground="#ffffff", font=("Segoe UI", 8))
        chk.pack(side="left", padx=10)
        # -------------------------------------------------

        self.os_garantia = tk.Text(frame, height=3, width=50, bd=1, relief="solid")
        self.os_garantia.pack(fill="x", pady=5)
        self.os_garantia.insert("1.0", "90 dias para serviços e 30 dias para peças.\nGarantia cobre defeitos de fabricação ou serviço.\nObrigatório apresentar este documento.")

        self.os_val_prod = self.create_field(frame, "Total Produtos (R$):")
        self.os_val_serv = self.create_field(frame, "Total Serviços (R$):")

        btn = tk.Button(frame, text="EMITIR O.S.", bg="#2c3e50", fg="white", font=("Segoe UI", 10, "bold"), 
                        relief="flat", pady=8, command=self.generate_pdf_os)
        btn.pack(pady=20, fill="x")

    # =========================================================================
    # TELA 2: ORÇAMENTO
    # =========================================================================
    def setup_orcamento_tab(self):
        frame = tk.Frame(self.tab_orcamento, padx=20, pady=20, bg="#ffffff")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Dados do Orçamento", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#27ae60").pack(anchor="w")

        self.orc_nome = self.create_field(frame, "Nome do Cliente:")
        self.orc_cpf = self.create_field(frame, "CPF:", mask_type="cpf")
        self.orc_tel = self.create_field(frame, "Telefone:", mask_type="tel")
        self.orc_end = self.create_field(frame, "Endereço:")
        
        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=10)
        
        self.orc_equip = self.create_field(frame, "Equipamento:")
        self.orc_problema = self.create_field(frame, "Problema Relatado:")
        
        tk.Label(frame, text="Serviços Propostos / Peças Necessárias:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5,0))
        self.orc_desc = tk.Text(frame, height=4, width=50, bd=1, relief="solid")
        self.orc_desc.pack(fill="x", pady=5)

        self.orc_validade = self.create_field(frame, "Validade do Orçamento:")
        self.orc_validade.insert(0, "15 dias")

        tk.Label(frame, text="Valores:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(10,0))
        self.orc_val_visita = self.create_field(frame, "Valor da Visita (R$):")
        self.orc_val_servicos = self.create_field(frame, "Valor Serviços/Peças (R$):")

        btn = tk.Button(frame, text="EMITIR ORÇAMENTO", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), 
                        relief="flat", pady=8, command=self.generate_pdf_orcamento)
        btn.pack(pady=20, fill="x")

    # =========================================================================
    # TELA 3: RECIBO
    # =========================================================================
    def setup_recibo_tab(self):
        frame = tk.Frame(self.tab_recibo, padx=20, pady=20, bg="#ffffff")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Dados do Recibo", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#195e38").pack(anchor="w")

        self.rec_data = self.create_field(frame, "Data do Recibo (DD/MM/AAAA):", mask_type="data")
        self.rec_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        self.rec_nome = self.create_field(frame, "Nome da Empresa / Pagador:")

        tk.Label(frame, text="Tipo de Documento:", font=("Segoe UI", 9), bg="#ffffff").pack(anchor="w", pady=(5,0))
        self.rec_tipo_doc = tk.StringVar(value="CNPJ")
        
        row_frame = tk.Frame(frame, bg="#ffffff")
        row_frame.pack(fill="x", anchor="w")
        
        r1 = tk.Radiobutton(row_frame, text="CNPJ", variable=self.rec_tipo_doc, value="CNPJ", bg="#ffffff", 
                            command=lambda: self.rec_doc_num.delete(0, tk.END))
        r1.pack(side="left", padx=(0,10))
        r2 = tk.Radiobutton(row_frame, text="CPF", variable=self.rec_tipo_doc, value="CPF", bg="#ffffff",
                            command=lambda: self.rec_doc_num.delete(0, tk.END))
        r2.pack(side="left")

        self.rec_doc_num = self.create_field(frame, "Número do Documento:", mask_type="doc_recibo")

        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=10)
        
        self.rec_valor = self.create_field(frame, "Valor (R$):")
        
        tk.Label(frame, text="Referente ao serviço de:", font=("Segoe UI", 9, "bold"), bg="#ffffff").pack(anchor="w", pady=(5,0))
        self.rec_desc = tk.Text(frame, height=5, width=50, bd=1, relief="solid")
        self.rec_desc.pack(fill="x", pady=5)
        
        btn = tk.Button(frame, text="EMITIR RECIBO", bg="#195e38", fg="white", font=("Segoe UI", 10, "bold"), 
                        relief="flat", pady=8, command=self.generate_pdf_recibo)
        btn.pack(pady=20, fill="x")

    # =========================================================================
    # FUNÇÕES PDF
    # =========================================================================
    def generate_pdf_os(self):
        # Verifica se a caixa de seleção está marcada
        termos_texto = self.os_garantia.get("1.0", tk.END).strip()
        if not self.os_garantia_check_var.get():
            termos_texto = "" # Envia vazio para não imprimir

        dados = {
            'titulo': "ORDEM DE SERVIÇO",
            'cor_titulo': colors.HexColor("#2c3e50"),
            'nome': self.os_nome.get(),
            'cpf': self.os_cpf.get(),
            'tel': self.os_tel.get(),
            'end': self.os_end.get(),
            'equip': self.os_equip.get(),
            'detalhe1_label': "Defeito Apresentado:",
            'detalhe1': self.os_defeito.get(),
            'detalhe2_label': "Parecer Técnico:",
            'detalhe2': self.os_parecer.get("1.0", tk.END).strip(),
            'val_prod': self.os_val_prod.get(),
            'val_serv': self.os_val_serv.get(),
            'termos': termos_texto, 
            'tipo': 'OS'
        }
        self.create_pro_pdf(dados)

    def generate_pdf_orcamento(self):
        dados = {
            'titulo': "ORÇAMENTO",
            'cor_titulo': colors.HexColor("#27ae60"),
            'nome': self.orc_nome.get(),
            'cpf': self.orc_cpf.get(),
            'tel': self.orc_tel.get(),
            'end': self.orc_end.get(),
            'equip': self.orc_equip.get(),
            'detalhe1_label': "Problema Relatado:",
            'detalhe1': self.orc_problema.get(),
            'detalhe2_label': "Descrição dos Serviços e Peças:",
            'detalhe2': self.orc_desc.get("1.0", tk.END).strip(),
            'val_visita': self.orc_val_visita.get(),
            'val_servicos': self.orc_val_servicos.get(),
            'termos': f"Validade: {self.orc_validade.get()}.\nValores sujeitos a alteração após o vencimento.",
            'tipo': 'ORC'
        }
        self.create_pro_pdf(dados)

    def create_pro_pdf(self, dados):
        if not dados['nome'] or not dados['equip']:
            messagebox.showwarning("Aviso", "Preencha pelo menos Nome e Equipamento.")
            return

        filename_only = f"{dados['tipo']}_{dados['nome'].replace(' ', '_')}_{datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
        if dados['tipo'] == 'OS':
            full_path = os.path.join(self.os_dir, filename_only)
        else:
            full_path = os.path.join(self.orc_dir, filename_only)

        c = canvas.Canvas(full_path, pagesize=A4)
        width, height = A4
        
        primary_color = dados['cor_titulo'] 
        secondary_bg = colors.HexColor("#f3f4f6")
        line_color = colors.HexColor("#d1d5db")
        text_color = colors.HexColor("#1f2937")

        c.setFillColor(primary_color)
        c.rect(0, 720, width, 122, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(30, 790, "LUCAS SALGADO") 
        c.setFont("Helvetica", 14)
        c.drawString(30, 770, "TÉCNICO DE INFORMÁTICA")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 30, 790, "CPF: 158.444.917-93")
        c.drawRightString(width - 30, 775, "Rua Simeão Fernandes, 70")
        c.drawRightString(width - 30, 760, "Campo Grande - RJ")
        c.drawRightString(width - 30, 745, f"Emissão: {datetime.now().strftime('%d/%m/%Y')}")

        c.setFillColor(colors.white)
        c.roundRect(30, 690, 250, 40, 5, fill=1, stroke=0)
        c.setFillColor(primary_color)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(45, 702, dados['titulo'])
        y = 660

        def draw_section_title(c, y, title):
            c.setFillColor(secondary_bg)
            c.rect(30, y, width-60, 25, fill=1, stroke=0)
            c.setFillColor(primary_color)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y+7, title.upper())
            return y - 20

        y = draw_section_title(c, y, "Dados do Cliente")
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Nome:")
        c.setFont("Helvetica", 10)
        c.drawString(80, y, dados['nome'])
        c.setFont("Helvetica-Bold", 10)
        c.drawString(350, y, "CPF/CNPJ:")
        c.setFont("Helvetica", 10)
        c.drawString(415, y, dados['cpf'])
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Endereço:")
        c.setFont("Helvetica", 10)
        c.drawString(95, y, dados['end'] if dados['end'] else "Não informado")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(350, y, "Telefone:")
        c.setFont("Helvetica", 10)
        c.drawString(405, y, dados['tel'])
        y -= 30

        y = draw_section_title(c, y, "Detalhes do Equipamento e Serviço")
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Equipamento:")
        c.setFont("Helvetica", 10)
        c.drawString(120, y, dados['equip'])
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, dados['detalhe1_label'])
        c.setFont("Helvetica", 10)
        c.drawString(40, y-15, dados['detalhe1'])
        y -= 35
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, dados['detalhe2_label'])
        c.setFont("Helvetica", 10)
        
        current_y = y - 15
        text_object = c.beginText(40, current_y)
        text_object.setFont("Helvetica", 10)
        text_object.setFillColor(text_color)
        
        descricao = dados['detalhe2']
        wrapper_width = 90
        lines = []
        for paragraph in descricao.split('\n'):
            while len(paragraph) > wrapper_width:
                split_index = paragraph[:wrapper_width].rfind(' ')
                if split_index == -1: split_index = wrapper_width
                lines.append(paragraph[:split_index])
                paragraph = paragraph[split_index:].strip()
            lines.append(paragraph)
            
        for line in lines:
            text_object.textLine(line)
            current_y -= 14
        
        c.drawText(text_object)
        y = current_y - 20

        y -= 10
        c.setFillColor(colors.HexColor("#fcfcfc"))
        c.setStrokeColor(line_color)
        c.roundRect(30, y-90, width-60, 100, 5, fill=1, stroke=1)
        
        text_y = y - 20
        c.setFillColor(text_color)
        
        if dados['tipo'] == 'OS':
            c.setFont("Helvetica", 10)
            c.drawString(50, text_y, "Produtos Utilizados:")
            c.drawRightString(width-50, text_y, f"R$ {dados.get('val_prod', '0,00')}")
            text_y -= 20
            c.drawString(50, text_y, "Serviços Prestados:")
            c.drawRightString(width-50, text_y, f"R$ {dados.get('val_serv', '0,00')}")
            text_y -= 10
            c.setStrokeColor(line_color)
            c.line(50, text_y, width-50, text_y)
            text_y -= 25
            
            try:
                v1 = float(dados['val_prod'].replace(',','.') or 0)
                v2 = float(dados['val_serv'].replace(',','.') or 0)
                total = f"{v1+v2:.2f}".replace('.', ',')
            except:
                total = "0,00"
            
            c.setFillColor(primary_color)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, text_y, "TOTAL A PAGAR")
            c.drawRightString(width-50, text_y, f"R$ {total}")
        
        else:
            c.setFont("Helvetica", 10)
            c.drawString(50, text_y, "Taxa de Visita Técnica:")
            c.drawRightString(width-50, text_y, f"R$ {dados.get('val_visita', '0,00')}")
            text_y -= 20
            c.drawString(50, text_y, "Valor Estimado Serviços/Peças:")
            c.drawRightString(width-50, text_y, f"R$ {dados.get('val_servicos', '0,00')}")
            text_y -= 10
            c.setStrokeColor(line_color)
            c.line(50, text_y, width-50, text_y)
            text_y -= 25
            try:
                v_visita = float(dados['val_visita'].replace(',','.') or 0)
                v_serv = float(dados['val_servicos'].replace(',','.') or 0)
                total_orc = f"{v_visita+v_serv:.2f}".replace('.', ',')
            except:
                total_orc = "0,00"

            c.setFillColor(primary_color)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, text_y, "TOTAL ESTIMADO")
            c.drawRightString(width-50, text_y, f"R$ {total_orc}")

        y -= 110
        c.setStrokeColor(line_color)
        c.setLineWidth(1)
        c.line(30, y, width-30, y)
        
        # --- SÓ IMPRIME OS TERMOS SE ELES EXISTIREM ---
        if dados['termos']:
            y -= 20
            c.setFillColor(colors.gray)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, y, "TERMOS E CONDIÇÕES / OBSERVAÇÕES")
            y -= 12
            c.setFont("Helvetica", 8)
            for line in dados['termos'].split('\n'):
                c.drawString(40, y, line)
                y -= 10
        # ----------------------------------------------

        y = 60
        c.setStrokeColor(colors.black)
        c.line(50, y, 250, y)
        c.line(340, y, 540, y)
        
        try:
            ass_path = resource_path("AssinaturaLucas.jpg")
            c.drawImage(ass_path, 395, 62, width=70, height=70, mask='auto')
        except Exception as e:
            print(f"Erro assinatura: {e}")

        c.setFillColor(text_color)
        c.setFont("Helvetica", 9)
        c.drawCentredString(150, y-15, "Assinatura do Cliente")
        c.drawCentredString(440, y-15, "Lucas Salgado do Nascimento")

        c.save()
        messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{full_path}")
        try:
            os.startfile(full_path) if os.name == 'nt' else None
        except:
            pass

    def generate_pdf_recibo(self):
        nome = self.rec_nome.get()
        tipo_doc = self.rec_tipo_doc.get()
        doc_num = self.rec_doc_num.get()
        valor = self.rec_valor.get()
        descricao_servico = self.rec_desc.get("1.0", tk.END).strip()
        data_input = self.rec_data.get()

        if not nome or not valor:
            messagebox.showwarning("Aviso", "Preencha Nome do pagador e Valor.")
            return

        filename_only = f"RECIBO_{nome.replace(' ', '_')}_{datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
        full_path = os.path.join(self.rec_dir, filename_only)

        c = canvas.Canvas(full_path, pagesize=A4)
        width, height = A4
        
        green_color = colors.HexColor("#195e38") 
        
        c.setFillColor(green_color)
        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2, height - 100, "Recibo de prestação de serviço")

        texto_base = f"Recebi da empresa {nome}, inscrita sob o {tipo_doc} {doc_num} o valor de R${valor} referente ao serviço de {descricao_servico}."
        
        c.setFont("Helvetica", 14)
        
        text_object = c.beginText(60, height - 200)
        text_object.setFont("Helvetica", 14)
        text_object.setFillColor(green_color)
        text_object.setLeading(20)

        wrapper_width = 65
        words = texto_base.split()
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > wrapper_width:
                current_line.pop()
                text_object.textLine(' '.join(current_line))
                current_line = [word]
        if current_line:
            text_object.textLine(' '.join(current_line))
        c.drawText(text_object)

        try:
            dt = datetime.strptime(data_input, "%d/%m/%Y")
            mes_extenso = MESES.get(dt.month, "MêsInválido")
            texto_data = f"RIO DE JANEIRO, {dt.day:02d} DE {mes_extenso} DE {dt.year}."
        except ValueError:
            texto_data = f"RIO DE JANEIRO, {data_input}."

        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - 400, texto_data)

        y_ass = 200
        
        try:
            ass_path = resource_path("AssinaturaLucas.jpg")
            c.drawImage(ass_path, (width/2) - 35, y_ass + 2, width=70, height=70, mask='auto')
        except Exception:
            pass

        c.setStrokeColor(colors.black)
        c.line(width/2 - 150, y_ass, width/2 + 150, y_ass)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, y_ass - 20, "Lucas Salgado do Nascimento")
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, y_ass - 38, "CPF 158.444.917-93")

        c.save()
        messagebox.showinfo("Sucesso", f"Recibo salvo em:\n{full_path}")
        try:
            os.startfile(full_path) if os.name == 'nt' else None
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaTecnicoApp(root)
    root.mainloop()