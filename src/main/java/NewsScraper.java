import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.time.DayOfWeek;
import java.time.LocalDate;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

public class NewsScraper {
    public static void main(String[] args) {
        try {
            Class.forName("org.sqlite.JDBC");
            Connection conn = DriverManager.getConnection("jdbc:sqlite:data/noticias.db");
            Statement stmt = conn.createStatement();
            stmt.executeUpdate("CREATE TABLE IF NOT EXISTS noticias (id INTEGER PRIMARY KEY, titulo TEXT, fecha TEXT, dia_semana TEXT, fuente TEXT)");

            insertarNoticias("https://elpais.com/ultimas-noticias/", "h2 a", "El País", conn);
            insertarNoticias("https://cnnespanol.cnn.com/", "span.container__headline-text[data-editable=\"headline\"]", "CNN", conn);
            insertarNoticias("https://www.bbc.com/mundo", "a[aria-label]", "BBC", conn);
            insertarNoticias("https://www.msnbc.com/", "h2 span", "MSNBC", conn);

            conn.close();
            System.out.println("Scraping completo.");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void insertarNoticias(String url, String selector, String fuente, Connection conn) {
        try {
            Document doc = Jsoup.connect(url).userAgent("Mozilla/5.0").get();
            Elements noticias = doc.select(selector);

            PreparedStatement pstmt = conn.prepareStatement("INSERT INTO noticias (titulo, fecha, dia_semana, fuente) VALUES (?, ?, ?, ?)");
            LocalDate hoy = LocalDate.now();
            String dia = DayOfWeek.from(hoy).toString();

            for (Element noticia : noticias) {
                String titulo;

                if (fuente.equals("BBC")) {
                    titulo = noticia.attr("aria-label").trim();
                } else {
                    titulo = noticia.text().trim();
                }

                if (titulo.isEmpty()) continue;

                System.out.println("[" + fuente + "] " + titulo);
                pstmt.setString(1, titulo);
                pstmt.setString(2, hoy.toString());
                pstmt.setString(3, dia);
                pstmt.setString(4, fuente);
                pstmt.executeUpdate();
            }
        } catch (Exception e) {
            System.out.println("Error en " + fuente);
        }
    }
}
