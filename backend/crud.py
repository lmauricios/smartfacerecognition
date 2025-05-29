import psycopg2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io  # Adicionado para manipulação de imagem em memória
import cv2  # Necessário para decodificar imagem para face_recognition
import face_recognition  # Necessário para extrair encodings
import numpy as np  # Necessário para manipulação de array de imagem
import os  # Para o exemplo de variáveis de ambiente (opcional)

# --- Configurações do Banco de Dados ---
# Idealmente, use variáveis de ambiente ou um arquivo de config seguro
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "reconhecimento_facial")
DB_USER = os.environ.get("DB_USER", "meu_usuario")
DB_PASS = os.environ.get("DB_PASS", "Innovate@V8")  # Mantenha senhas fora do código em produção

# Diretório para salvar as imagens originais do CRUD
CRUD_IMAGES_DIR = "imagens_crud"

conn = None
cur = None


def setup_db_connection():
    """Estabelece a conexão com o banco de dados."""
    global conn, cur
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        print("Conexão com o banco de dados estabelecida.")
        return True
    except psycopg2.Error as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}")
        return False


def close_db_connection():
    """Fecha a conexão com o banco de dados."""
    global conn, cur
    if cur:
        cur.close()
        print("Cursor do banco de dados fechado.")
    if conn:
        conn.close()
        print("Conexão com o banco de dados fechada.")


def inserir_pessoa():
    if not cur:
        messagebox.showerror("Erro de Banco de Dados", "Sem conexão com o banco de dados.")
        return

    nome = nome_entry.get()
    caminho_foto = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.JPG;*.JPEG")])

    if nome and caminho_foto:
        try:
            # Garante que o diretório de imagens do CRUD exista
            if not os.path.exists(CRUD_IMAGES_DIR):
                os.makedirs(CRUD_IMAGES_DIR)

            # Ler a imagem para extrair o encoding
            with open(caminho_foto, "rb") as file:
                image_bytes = file.read()

            nparr = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_bgr is None:
                messagebox.showerror("Erro de Imagem", "Não foi possível decodificar a imagem selecionada.")
                return

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(img_rgb)

            if not encodings:
                messagebox.showwarning("Aviso", f"Nenhum encoding facial encontrado na imagem para {nome}.")
                return

            face_encoding_binary = psycopg2.Binary(encodings[0].tobytes())

            # Salvar a imagem original localmente para o CRUD
            _, ext = os.path.splitext(caminho_foto)
            nome_arquivo_crud = (
                f"{nome.replace(' ', '_')}_{int(np.random.randint(1000, 9999))}{ext}"  # Nome de arquivo único simples
            )
            caminho_imagem_crud_salva = os.path.join(CRUD_IMAGES_DIR, nome_arquivo_crud)
            with open(caminho_imagem_crud_salva, "wb") as f_out:
                f_out.write(image_bytes)

            cur.execute(  # Adicionada a coluna imagem_path
                "INSERT INTO pessoas (nome_pessoa, face_encoding, imagem_path) VALUES (%s, %s, %s) ON CONFLICT (nome_pessoa) DO UPDATE SET face_encoding = EXCLUDED.face_encoding, imagem_path = EXCLUDED.imagem_path",
                (nome, face_encoding_binary, caminho_imagem_crud_salva),
            )
            conn.commit()
            messagebox.showinfo("Sucesso", f"Pessoa '{nome}' inserida/atualizada com encoding facial!")
            nome_entry.delete(0, tk.END)
        except FileNotFoundError:
            messagebox.showerror("Erro", f"Arquivo não encontrado: {caminho_foto}")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao inserir pessoa: {e}")
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")
    else:
        messagebox.showerror("Erro", "Nome ou foto ausente!")


def buscar_pessoa():
    if not cur:
        messagebox.showerror("Erro de Banco de Dados", "Sem conexão com o banco de dados.")
        return

    nome = nome_entry.get()
    if not nome:
        messagebox.showerror("Erro", "O nome para busca não pode estar vazio.")
        return

    try:
        cur.execute(
            "SELECT nome_pessoa, imagem_path FROM pessoas WHERE nome_pessoa = %s", (nome,)
        )  # Buscar imagem_path
        pessoa = cur.fetchone()

        if pessoa:
            nome_pessoa_db, caminho_imagem_crud = pessoa
            if caminho_imagem_crud and os.path.exists(caminho_imagem_crud):
                img = Image.open(caminho_imagem_crud)
                img.thumbnail((200, 200))
                img_tk = ImageTk.PhotoImage(img)

                img_label.config(image=img_tk)
                img_label.image = img_tk
                messagebox.showinfo("Pessoa Encontrada", f"Pessoa: {nome_pessoa_db}")
            else:
                img_label.config(image=None)
                img_label.image = None
                messagebox.showinfo(
                    "Pessoa Encontrada",
                    f"Pessoa: {nome_pessoa_db}\n(Imagem original não encontrada ou não registrada para o CRUD)",
                )

        else:
            messagebox.showinfo("Informação", "Pessoa não encontrada.")
            img_label.config(image=None)  # Limpar imagem anterior
            img_label.image = None
    except psycopg2.Error as e:
        messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar pessoa: {e}")
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao buscar: {e}")


def deletar_pessoa():
    if not cur:
        messagebox.showerror("Erro de Banco de Dados", "Sem conexão com o banco de dados.")
        return

    nome = nome_entry.get()
    if not nome:
        messagebox.showerror("Erro", "O nome para deleção não pode estar vazio.")
        return

    if messagebox.askyesno("Confirmar Deleção", f"Tem certeza que deseja excluir '{nome}'?"):
        try:
            # Opcional: buscar o caminho da imagem para deletar o arquivo local também
            cur.execute("SELECT imagem_path FROM pessoas WHERE nome_pessoa = %s", (nome,))
            resultado_path = cur.fetchone()

            cur.execute("DELETE FROM pessoas WHERE nome_pessoa = %s", (nome,))
            conn.commit()
            if cur.rowcount > 0:
                if resultado_path and resultado_path[0] and os.path.exists(resultado_path[0]):
                    try:
                        os.remove(resultado_path[0])
                        print(f"Arquivo de imagem local {resultado_path[0]} deletado.")
                    except OSError as e_file:
                        print(f"Erro ao deletar arquivo de imagem local {resultado_path[0]}: {e_file}")
                messagebox.showinfo("Sucesso", f"Pessoa '{nome}' excluída com sucesso!")
                nome_entry.delete(0, tk.END)  # Limpa o campo nome
                img_label.config(image=None)  # Limpar imagem
                img_label.image = None
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao deletar pessoa: {e}")
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao deletar: {e}")


def on_closing():
    """Função chamada ao fechar a janela."""
    if messagebox.askokcancel("Sair", "Você quer sair da aplicação?"):
        close_db_connection()
        root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cadastro de Pessoas")

    # Tenta conectar ao banco de dados ao iniciar
    db_ready = setup_db_connection()

    # Widgets de entrada e botões
    tk.Label(root, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    nome_entry = tk.Entry(root, width=30)
    nome_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

    btn_inserir = tk.Button(root, text="Inserir Pessoa", command=inserir_pessoa)
    btn_inserir.grid(row=1, column=0, padx=5, pady=10, sticky="ew")

    btn_buscar = tk.Button(root, text="Buscar Pessoa", command=buscar_pessoa)
    btn_buscar.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

    btn_deletar = tk.Button(root, text="Deletar Pessoa", command=deletar_pessoa)
    btn_deletar.grid(row=1, column=2, padx=5, pady=10, sticky="ew")

    img_label = tk.Label(root)  # Para exibir a imagem
    img_label.grid(row=2, column=0, columnspan=3, padx=5, pady=10)

    # Configura o fechamento da janela para chamar on_closing
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Desabilita botões se o DB não estiver pronto
    if not db_ready:
        btn_inserir.config(state=tk.DISABLED)
        btn_buscar.config(state=tk.DISABLED)
        btn_deletar.config(state=tk.DISABLED)
        # A mensagem de erro já foi exibida por setup_db_connection()
        # messagebox.showwarning("Aviso de Banco de Dados",
        #                        "Não foi possível conectar ao banco. As funcionalidades estarão limitadas.")

    # Configura a expansão das colunas para preencher o espaço
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)

    root.mainloop()

    # A conexão é fechada pela função on_closing.
    # Se o mainloop terminar por outra razão (improvável sem on_closing),
    # a conexão pode não ser fechada. on_closing é a forma mais garantida para Tkinter.
    # Se setup_db_connection falhou, conn e cur podem ser None.
    # A função close_db_connection() já lida com isso.
    # Se a janela for fechada abruptamente sem passar por on_closing,
    # a conexão pode permanecer aberta até o script Python terminar.
    # Para garantir o fechamento em mais cenários, poderia-se usar `atexit`
    # import atexit
    # atexit.register(close_db_connection)
    # Mas para Tkinter, root.protocol é o método preferido.
