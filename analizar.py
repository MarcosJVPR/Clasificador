import sqlite3
import pandas as pd
import sys
import joblib
import json
from pathlib import Path
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report

modo_entrenar = "--entrenar" in sys.argv
modo_predecir = "--predecir" in sys.argv

if modo_entrenar:
    dataset_path = Path("dataset_news.csv")
    if not dataset_path.exists():
        print("dataset_news.csv no encontrado.")
        sys.exit(1)

    df = pd.read_csv(dataset_path)
    df = df[df["etiqueta"].notna() & (df["etiqueta"] != "")]

    X = df["titulo"]
    y = df["etiqueta"]

    vectorizer = CountVectorizer()
    X_vect = vectorizer.fit_transform(X)

    modelo = MultinomialNB()
    modelo.fit(X_vect, y)

    pred = modelo.predict(X_vect)
    print(classification_report(y, pred))

    joblib.dump(modelo, "modelo_entrenado.pkl")
    joblib.dump(vectorizer, "vectorizer.pkl")
    print("Modelo entrenado y guardado.")
    sys.exit(0)

if modo_predecir:
    modelo_path = Path("modelo_entrenado.pkl")
    vectorizer_path = Path("vectorizer.pkl")

    if not modelo_path.exists() or not vectorizer_path.exists():
        print("Modelo no entrenado. Ejecuta primero con --entrenar.")
        sys.exit(1)

    modelo = joblib.load(modelo_path)
    vectorizer = joblib.load(vectorizer_path)

    conn = sqlite3.connect('data/noticias.db')
    df = pd.read_sql_query("SELECT * FROM noticias", conn)
    conn.close()

    X_nuevas = df["titulo"]
    X_vect = vectorizer.transform(X_nuevas)
    predicciones = modelo.predict(X_vect)

    df["categoria"] = predicciones
    df.to_csv("resultado_con_predicciones.csv", index=False)
    df.to_json("static/data.json", orient="records", force_ascii=False)

    conteo = df["categoria"].value_counts()
    estado = "positivo" if conteo.get("positivo", 0) >= conteo.get("negativo", 0) else "negativo"

    with open("estado_dia.js", "w", encoding="utf-8") as f:
        f.write(f'document.body.className = "{estado}";\n')

    if "fuente" in df.columns:
        resumen = df.groupby(["fuente", "categoria"]).size().unstack(fill_value=0)
        resumen.to_csv("resumen_por_fuente.csv")
        resumen.to_json("static/resumen_por_fuente.json", orient="index")

        porcentajes = resumen.div(resumen.sum(axis=1), axis=0).round(2)
        porcentajes.to_csv("porcentajes_por_fuente.csv")
        porcentajes.to_json("static/porcentajes_por_fuente.json", orient="index")

    print("Clasificación completada. Archivos generados:")
    print("- resultado_con_predicciones.csv")
    print("- static/data.json")
    print("- static/resumen_por_fuente.json")
    print("- static/porcentajes_por_fuente.json")
    print("- scripts/estado_dia.js")
    sys.exit(0)
