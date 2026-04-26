# app.py - AI Service (version simple sans RabbitMQ)

from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Créer l'application Flask
app = Flask(__name__)


def calculate_score(job_description, cv_text):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([job_description, cv_text])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(float(similarity), 2)

# ==================== ENDPOINT 1 : ANALYSE UN SEUL CV ====================
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Compare une offre d'emploi et un CV
    Reçoit : { "job_description": "...", "cv_text": "..." }
    Retourne : { "score": 0.85 }
    """
    
    # 1. Récupérer les données envoyées par l'utilisateur
    data = request.get_json()
    job_description = data.get('job_description', '')
    cv_text = data.get('cv_text', '')
    
    # 2. Vérifier que les données existent
    if not job_description or not cv_text:
        return jsonify({'error': 'job_description et cv_text sont requis'}), 400
    
    # 3. Créer un vecteur TF-IDF
    #    Transforme les textes en nombres
    
    # 4. Appliquer aux deux textes
    
    # 5. Calculer la similarité cosinus (score entre 0 et 1)
    
    # 6. Arrondir à 2 décimales
    
    score = calculate_score(job_description, cv_text)
    # 7. Retourner le score
    return jsonify({'score': score})

# ==================== ENDPOINT 2 : CLASSEMENT POUR UNE OFFRE ====================
@app.route('/match/<job_id>', methods=['GET'])
def match_job(job_id):
    """
    Pour l'instant, version simplifiée sans appels aux autres services
    On va tester avec des données en dur
    """
    
    # Données de test (pour l'instant, sans Job Service ni CV Service)
    job_description = "Développeur Python avec Flask et Docker"
    
    cvs = [
        {"id": 1, "candidate_name": "Jean", "text": "Je connais Python et Flask"},
        {"id": 2, "candidate_name": "Marie", "text": "Expert en Java et Spring"},
        {"id": 3, "candidate_name": "Pierre", "text": "Python, Docker, Kubernetes"},
    ]
    
    # Calculer le score pour chaque CV
    results = []
    for cv in cvs:
        # Appeler notre propre endpoint /analyze
        score_res = requests.post('http://localhost:5004/analyze', json={
            'job_description': job_description,
            'cv_text': cv['text']
        })
        score = score_res.json()['score']
        
        results.append({
            'candidate_name': cv['candidate_name'],
            'score': score
        })
    
    # Trier par score décroissant (du meilleur au moins bon)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify(results)

# ==================== ENDPOINT POUR VÉRIFIER QUE LE SERVICE TOURNE ====================
@app.route('/health', methods=['GET'])
def health():
    """Vérifier que le service est en vie"""
    return jsonify({'status': 'OK', 'message': 'AI Service fonctionne !'})

# ==================== DÉMARRAGE DU SERVEUR ====================
if __name__ == '__main__':
    print("🚀 Démarrage de l'AI Service...")
    print("📡 API disponible sur http://localhost:5004")
    print("📍 Endpoints :")
    print("   POST /analyze  - Analyser un CV")
    print("   GET  /match/1  - Classement (test)")
    print("   GET  /health   - Vérifier l'état")
    app.run(host='0.0.0.0', port=5004, debug=True)
