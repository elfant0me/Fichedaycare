import streamlit as st
import sqlite3
import json
from datetime import datetime
import hashlib
import base64
from io import BytesIO
import pandas as pd
from PIL import Image

# Set page config
st.set_page_config(
    page_title="Fiche d'Assiduité - Garderie Familiale",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database initialization
@st.cache_resource
def init_db():
    conn = sqlite3.connect('garderie.db', check_same_thread=False)
    c = conn.cursor()

    # Create forms table
    c.execute('''CREATE TABLE IF NOT EXISTS forms (
        id TEXT PRIMARY KEY,
        bureau TEXT,
        enfant TEXT,
        parent TEXT,
        rsge TEXT,
        date_fin TEXT,
        attendance TEXT,
        payments TEXT,
        parent_signature TEXT,
        rsge_signature TEXT,
        created_date TEXT,
        status TEXT,
        parent_signed INTEGER DEFAULT 0,
        parent_signed_date TEXT
    )''')

    conn.commit()
    conn.close()
    return True

# Database operations
def save_form_to_db(form_id, form_data):
    conn = sqlite3.connect('garderie.db', check_same_thread=False)
    c = conn.cursor()

    c.execute('''INSERT OR REPLACE INTO forms 
                 (id, bureau, enfant, parent, rsge, date_fin, attendance, payments, 
                  parent_signature, rsge_signature, created_date, status, parent_signed, parent_signed_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (form_id, form_data.get('bureau', ''), form_data.get('enfant', ''),
               form_data.get('parent', ''), form_data.get('rsge', ''), form_data.get('date_fin', ''),
               json.dumps(form_data.get('attendance', [])), json.dumps(form_data.get('payments', [])),
               form_data.get('parent_signature', ''), form_data.get('rsge_signature', ''),
               form_data.get('created_date', ''), form_data.get('status', 'draft'),
               form_data.get('parent_signed', 0), form_data.get('parent_signed_date', '')))

    conn.commit()
    conn.close()

def get_form_from_db(form_id):
    conn = sqlite3.connect('garderie.db', check_same_thread=False)
    c = conn.cursor()

    c.execute('SELECT * FROM forms WHERE id = ?', (form_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'bureau': row[1],
            'enfant': row[2],
            'parent': row[3],
            'rsge': row[4],
            'date_fin': row[5],
            'attendance': json.loads(row[6]) if row[6] else [],
            'payments': json.loads(row[7]) if row[7] else [],
            'parent_signature': row[8],
            'rsge_signature': row[9],
            'created_date': row[10],
            'status': row[11],
            'parent_signed': row[12],
            'parent_signed_date': row[13]
        }
    return None

def get_all_forms():
    conn = sqlite3.connect('garderie.db', check_same_thread=False)
    c = conn.cursor()

    c.execute('SELECT * FROM forms ORDER BY created_date DESC')
    rows = c.fetchall()
    conn.close()

    forms = {}
    for row in rows:
        forms[row[0]] = {
            'id': row[0],
            'bureau': row[1],
            'enfant': row[2],
            'parent': row[3],
            'rsge': row[4],
            'date_fin': row[5],
            'attendance': json.loads(row[6]) if row[6] else [],
            'payments': json.loads(row[7]) if row[7] else [],
            'parent_signature': row[8],
            'rsge_signature': row[9],
            'created_date': row[10],
            'status': row[11],
            'parent_signed': row[12],
            'parent_signed_date': row[13]
        }
    return forms

def delete_form_from_db(form_id):
    conn = sqlite3.connect('garderie.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('DELETE FROM forms WHERE id = ?', (form_id,))
    conn.commit()
    conn.close()

# Check admin password
def check_admin_password(password):
    return password == "garderiemariemeli1423"

# Initialize database
init_db()

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }

    .form-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }

    .legend-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }

    .legend-item {
        background: white;
        color: #333;
        padding: 0.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }

    .admin-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("🏠 Navigation")
page = st.sidebar.selectbox("Choisir une page", ["📋 Nouvelle Fiche", "🔐 Administration"])

if page == "📋 Nouvelle Fiche":
    # Form page
    st.markdown('<div class="form-container"><h1>📋 Fiche d\'Assiduité</h1><p>Garderie en Milieu Familial - Signature Électronique</p></div>', unsafe_allow_html=True)

    # Check if loading existing form
    form_id_query = st.query_params.get("id")
    form_data = {}
    if form_id_query:
        # Ensure form_id_query is treated as a list if it's a single value
        form_id_list = form_id_query if isinstance(form_id_query, list) else [form_id_query]
        if form_id_list:
            form_data = get_form_from_db(form_id_list[0]) or {}

    # Basic Information
    st.subheader("ℹ️ Informations de Base")
    col1, col2 = st.columns(2)

    with col1:
        bureau = st.text_input("Nom du bureau coordonnateur", value=form_data.get('bureau', ''), disabled=bool(form_data))
        enfant = st.text_input("Nom de l'enfant", value=form_data.get('enfant', ''), disabled=bool(form_data))
        parent = st.text_input("Nom du parent", value=form_data.get('parent', ''), disabled=bool(form_data))

    with col2:
        rsge = st.text_input("Nom de la RSGE", value=form_data.get('rsge', ''), disabled=bool(form_data))
        date_fin_value = None
        if form_data.get('date_fin'):
            try:
                date_fin_value = datetime.strptime(form_data.get('date_fin'), '%Y-%m-%d').date()
            except ValueError:
                date_fin_value = datetime.now().date() # Fallback to today if format is wrong
        
        date_fin = st.date_input("Date de fin de fréquentation", value=date_fin_value, disabled=bool(form_data))

    # Legend
    st.subheader("📖 Légende des Codes")
    st.markdown("""
    <div class="legend-grid">
        <div class="legend-item"><strong>P:</strong> Présence 1 jour</div>
        <div class="legend-item"><strong>P½:</strong> Présence ½ jour</div>
        <div class="legend-item"><strong>A:</strong> Absence 1 jour</div>
        <div class="legend-item"><strong>A½:</strong> Absence ½ jour</div>
        <div class="legend-item"><strong>R:</strong> Enfant remplaçant 1 jour</div>
        <div class="legend-item"><strong>R½:</strong> Enfant remplaçant ½ jour</div>
        <div class="legend-item"><strong>F:</strong> 1 jour fermeture non subventionné</div>
        <div class="legend-item"><strong>AN:</strong> 1 journée non déterminée APSS</div>
    </div>
    """, unsafe_allow_html=True)

    # Attendance Grid
    st.subheader("📅 Assiduité")
    attendance_data = form_data.get('attendance', [])

    # Store attendance data in session state to persist across reruns
    if 'attendance_grid_state' not in st.session_state:
        st.session_state.attendance_grid_state = {}

    for week in range(4):
        st.write(f"**Semaine {week + 1}**")
        week_data = attendance_data[week] if week < len(attendance_data) else {'startDate': '', 'days': [''] * 7}

        col_date, *day_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1])

        with col_date:
            start_date_val = None
            if week_data.get('startDate'):
                try:
                    start_date_val = datetime.strptime(week_data.get('startDate'), '%Y-%m-%d').date()
                except ValueError:
                    start_date_val = datetime.now().date() # Fallback

            start_date = st.date_input(f"Début semaine {week + 1}", 
                                     value=start_date_val,
                                     key=f"start_date_{week}",
                                     disabled=bool(form_data))
            st.session_state.attendance_grid_state[f"start_date_{week}"] = start_date

        days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        options = ['', 'P', 'P½', 'A', 'A½', 'R', 'R½', 'F', 'F½', 'AN', 'AD', 'L', 'S', 'S½']

        for i, (day_col, day_name) in enumerate(zip(day_cols, days)):
            with day_col:
                current_value = week_data.get('days', [''] * 7)[i] if i < len(week_data.get('days', [])) else ''
                
                # Set default index based on current_value, handle cases where value might not be in options
                default_index = options.index(current_value) if current_value in options else 0
                
                selected_day = st.selectbox(day_name, options, 
                                            index=default_index,
                                            key=f"day_{week}_{i}",
                                            disabled=bool(form_data))
                st.session_state.attendance_grid_state[f"day_{week}_{i}"] = selected_day

    # Payments
    st.subheader("💳 Confirmation du paiement")
    payments_data = form_data.get('payments', [])

    if 'payment_state' not in st.session_state:
        st.session_state.payment_state = {}

    for i in range(4):
        payment_data = payments_data[i] if i < len(payments_data) else {'date': '', 'amount': '', 'balance': ''}
        col1, col2, col3 = st.columns(3)

        with col1:
            payment_date_val = None
            if payment_data.get('date'):
                try:
                    payment_date_val = datetime.strptime(payment_data.get('date'), '%Y-%m-%d').date()
                except ValueError:
                    payment_date_val = datetime.now().date() # Fallback

            payment_date = st.date_input(f"Date paiement {i+1}", 
                                        value=payment_date_val, 
                                        key=f"payment_date_{i}",
                                        disabled=bool(form_data))
            st.session_state.payment_state[f"payment_date_{i}"] = payment_date

        with col2:
            payment_amount = st.number_input(f"Montant payé ${i+1}", value=float(payment_data.get('amount', 0)) if payment_data.get('amount') else 0.0, key=f"payment_amount_{i}", disabled=bool(form_data))
            st.session_state.payment_state[f"payment_amount_{i}"] = payment_amount

        with col3:
            payment_balance = st.number_input(f"Solde à payer ${i+1}", value=float(payment_data.get('balance', 0)) if payment_data.get('balance') else 0.0, key=f"payment_balance_{i}", disabled=bool(form_data))
            st.session_state.payment_state[f"payment_balance_{i}"] = payment_balance

    # Signature section
    st.subheader("✍️ Signature du Parent")
    st.write("**Attestation :** J'atteste que les renseignements inscrits sur cette fiche d'assiduité correspondent à la présence réelle de mon enfant et aux contributions réduites payées et à payer.")

    is_form_signed = form_data.get('parent_signed', 0) == 1

    if not is_form_signed:
        from streamlit_drawable_canvas import st_canvas

        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0.0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#ffffff",
            height=150,
            width=500,
            drawing_mode="freedraw",
            key="signature_canvas",
        )

        if st.button("✅ Signer et Envoyer", type="primary", use_container_width=True):
            if canvas_result.image_data is not None:
                # Save form data
                form_id_to_save = form_data.get('id', f"form_{int(datetime.now().timestamp())}")

                # Convert canvas to base64
                img_buffer = BytesIO()
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                img.save(img_buffer, format='PNG')
                img_str = base64.b64encode(img_buffer.getvalue()).decode()

                # Collect all form data from inputs and session state
                new_form_data = {
                    'id': form_id_to_save,
                    'bureau': bureau,
                    'enfant': enfant,
                    'parent': parent,
                    'rsge': rsge,
                    'date_fin': str(date_fin) if date_fin else '',
                    'attendance': [],
                    'payments': [],
                    'parent_signature': f"data:image/png;base64,{img_str}",
                    'rsge_signature': form_data.get('rsge_signature', ''), # Keep existing if any
                    'created_date': form_data.get('created_date', datetime.now().isoformat()),
                    'status': 'signed',
                    'parent_signed': 1,
                    'parent_signed_date': datetime.now().isoformat()
                }

                # Collect attendance data from session state
                for week in range(4):
                    week_data = {
                        'startDate': str(st.session_state.attendance_grid_state.get(f"start_date_{week}", '')),
                        'days': [st.session_state.attendance_grid_state.get(f"day_{week}_{day}", '') for day in range(7)]
                    }
                    new_form_data['attendance'].append(week_data)

                # Collect payment data from session state
                for i in range(4):
                    payment_data = {
                        'date': str(st.session_state.payment_state.get(f"payment_date_{i}", '')),
                        'amount': st.session_state.payment_state.get(f"payment_amount_{i}", 0),
                        'balance': st.session_state.payment_state.get(f"payment_balance_{i}", 0)
                    }
                    new_form_data['payments'].append(payment_data)

                save_form_to_db(form_id_to_save, new_form_data)
                st.success("✅ Formulaire signé et envoyé avec succès !")
                st.balloons()
                # Optionally, disable the form or redirect
                # st.rerun() # This might be needed to refresh the UI to show as signed
            else:
                st.error("Veuillez signer avant d'envoyer le formulaire.")
    else:
        st.success("✅ Formulaire déjà signé et envoyé")
        if form_data.get('parent_signature'):
            st.image(form_data['parent_signature'], caption="Signature du parent", width=300)

elif page == "🔐 Administration":
    st.title("🔐 Administration")

    # Authentication state management
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.subheader("Connexion Administration")
        password = st.text_input("Mot de passe", type="password", key="admin_password")

        if st.button("Se connecter"):
            if check_admin_password(password):
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Gestion des Fiches")
        with col2:
            if st.button("🚪 Déconnexion"):
                st.session_state.admin_authenticated = False
                st.rerun()

        # Load all forms
        forms = get_all_forms()

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Nouvelle Fiche", use_container_width=True):
                # Clear query params to start a new form
                st.query_params["id"] = None 
                st.switch_page("app.py")
        with col2:
            if st.button("📊 Exporter Données", use_container_width=True):
                if forms:
                    # Create DataFrame for export
                    export_data = []
                    for form_id, form in forms.items():
                        export_data.append({
                            'ID': form_id,
                            'Enfant': form.get('enfant', ''),
                            'Parent': form.get('parent', ''),
                            'RSGE': form.get('rsge', ''),
                            'Bureau': form.get('bureau', ''),
                            'Date Fin': form.get('date_fin', ''),
                            'Statut': form.get('status', ''),
                            'Date Création': form.get('created_date', ''),
                            'Signé': 'Oui' if form.get('parent_signed') else 'Non'
                        })

                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f"fiches_assiduite_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

        # Display forms
        if forms:
            st.subheader(f"📁 Fiches Enregistrées ({len(forms)})")

            for form_id, form in forms.items():
                with st.container():
                    st.markdown('<div class="admin-card">', unsafe_allow_html=True)

                    col1, col2, col3 = st.columns([3, 1, 2])

                    with col1:
                        st.write(f"**{form.get('enfant', 'Sans nom')}**")
                        st.write(f"Parent: {form.get('parent', 'Non spécifié')}")
                        st.write(f"RSGE: {form.get('rsge', 'Non spécifié')}")
                        st.write(f"Créé: {form.get('created_date', '')[:10]}")

                    with col2:
                        status = "✅ Signé" if form.get('status') == 'signed' else "📝 Brouillon"
                        st.write(f"**Statut:** {status}")

                    with col3:
                        col_view, col_del = st.columns(2)
                        with col_view:
                            if st.button("👁️ Voir", key=f"view_{form_id}", use_container_width=True):
                                st.query_params["id"] = form_id
                                st.switch_page("app.py")
                        with col_del:
                            if st.button("🗑️ Supprimer", key=f"delete_{form_id}", use_container_width=True):
                                delete_form_from_db(form_id)
                                st.success(f"Fiche {form_id} supprimée")
                                st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Aucune fiche enregistrée pour le moment.")

if __name__ == "__main__":
    # The app is now driven by Streamlit's execution model.
    # No explicit Flask or threading setup needed here.
    pass