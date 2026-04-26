# AI Service - Smart CV Matcher

## Description
Ce service calcule un score de similarité entre une offre d'emploi et un CV en utilisant TF-IDF et la similarité cosinus.

## Lancer le service

```bash
pip install -r requirements.txt
python app.py


Endpoint principal
URL : POST /analyze

Format à envoyer (JSON) :
{
  "job_description": "Développeur Python avec Flask",
  "cv_text": "Je connais Python et Flask"
}
Format retourné (JSON): 
{
  "score": 0.85
}

Port
5004
Exemple d'appel depuis un autre service: 
import requests

score_res = requests.post("http://localhost:5004/analyze", json={
    "job_description": job_desc,
    "cv_text": cv_text
})
score = score_res.json()["score"]