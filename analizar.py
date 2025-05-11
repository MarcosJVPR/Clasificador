import sqlite3
import pandas as pd
import sys
import joblib
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

    conteo = df["categoria"].value_counts()
    estado = "positivo" if conteo.get("positivo", 0) >= conteo.get("negativo", 0) else "negativo"

    with open("estado_dia.js", "w", encoding="utf-8") as f:
        f.write(f'document.body.className = "{estado}";\n')

    def colorear_fila(row):
        clase = "positivo" if row["categoria"] == "positivo" else "negativo"
        return f'<tr class="{clase}"><td>{row["titulo"]}</td><td>{row["fuente"]}</td><td>{row["categoria"]}</td></tr>'

    filas_html = "\n".join(df.apply(colorear_fila, axis=1))
    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Noticias Clasificadas</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-image: url('https://images.pexels.com/photos/518543/pexels-photo-518543.jpeg?auto=compress&cs=tinysrgb&w=800');
      background-position: center;
      background-attachment: fixed;
      padding: 40px;
    }}
    h1 {{
      text-align: center;
      margin-bottom: 30px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
    }}
    th, td {{
      border: 1px solid #ccc;
      padding: 10px;
      text-align: left;
    }}
    th {{
      background-color: #333;
      color: white;
    }}
    tr.positivo {{
      background-color: #d4fcd4;
    }}
    tr.negativo {{
      background-color: #ffd5d5;
    }}
  </style>
</head>
<body>
  <h1>Noticias Clasificadas ({estado.upper()})</h1>
  <table>
    <thead>
      <tr><th>Título</th><th>Fuente</th><th>Categoría</th></tr>
    </thead>
    <tbody>
      {filas_html}
    </tbody>
  </table>
</body>
</html>"""

    with open("noticias_resumen.html", "w", encoding="utf-8") as f:
        f.write(html_completo)

    if "fuente" in df.columns:
        conteo = df.groupby(["fuente", "categoria"]).size().unstack(fill_value=0)
        porcentajes = conteo.div(conteo.sum(axis=1), axis=0).round(2)

        conteo.to_csv("resultado_resumen.csv")
        porcentajes.to_csv("resultado_porcentajes.csv")

        with open("resumen_por_fuente.html", "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Resumen por Fuente</title>
  <style>
    body {{ font-family: Arial; padding: 30px; background: #f5f5f5; }}
    h1 {{ text-align: center; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
    th {{ background: #222; color: white; }}
  </style>
</head>
<body>
  <h1>Noticias por Fuente y Categoría</h1>
  {conteo.to_html()}
</body>
</html>""")

        with open("porcentajes_por_fuente.html", "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Porcentajes por Fuente</title>
  <style>
    body {{ font-family: Arial; padding: 30px; background: #f5f5f5; }}
    h1 {{ text-align: center; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
    th {{ background: #333; color: white; }}
  </style>
</head>
<body>
  <h1>Distribución Relativa de Categorías por Fuente</h1>
  {porcentajes.to_html()}
</body>
</html>""")

    print("Clasificación completada:")
    print(conteo)
    print("Archivos generados:")
    print("- resultado_con_predicciones.csv")
    print("- estado_dia.js")
    print("- noticias_resumen.html")
    print("- resumen_por_fuente.html")
    print("- porcentajes_por_fuente.html")
    sys.exit(0)

conn = sqlite3.connect('data/noticias.db')
df = pd.read_sql_query("SELECT * FROM noticias", conn)
conn.close()

print("Noticias totales:", len(df))
if "fuente" in df.columns and "dia_semana" in df.columns:
    resumen = df.groupby(["fuente", "dia_semana"]).size().unstack(fill_value=0)
    print("\nResumen por fuente y día:")
    print(resumen)
