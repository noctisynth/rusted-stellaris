// Invoke the user's installed RW 1.15 parsers; no engine code is distributed.
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import com.corrodinggames.rts.game.units.custom.ag;
import com.corrodinggames.rts.game.units.custom.bb;
import com.corrodinggames.rts.gameFramework.utility.ab;

public class LocalizationProbe {
    // Obfuscated jars contain class/package name collisions; reflection avoids
    // javac treating game.b and gameFramework.h as classes instead of packages.
    static void locale(String lang) throws Exception {
        Class<?> type = Class.forName("com.corrodinggames.rts.gameFramework.h.a");
        type.getField("d").set(null, lang);
        type.getField("c").setInt(null, type.getField("c").getInt(null) + 1);
    }
    static void expect(String target, String lang, String actual, String expected) {
        if (!Objects.equals(actual, expected))
            throw new AssertionError(target + " [" + lang + "]: " + actual + " != " + expected);
    }
    public static void main(String[] args) throws Exception {
        Map<String, ab> configs = new HashMap<>();
        int count = 0;
        for (String line : Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8)) {
            String[] v = line.split("\t", -1);
            String file = v[0], section = v[1], key = v[2], lang = v[3];
            String expected = new String(Base64.getDecoder().decode(v[4]), StandardCharsets.UTF_8);
            locale(lang);
            ab config = configs.get(file);
            if (config == null) {
                config = new ab(Files.newInputStream(Paths.get(file)), file);
                configs.put(file, config);
            }
            String actual = key.startsWith("show")
                ? ag.a(null, config, section, key, null).b(null)
                : config.a(section, key, (String)null, false).b();
            expect(file + "::" + section + "::" + key, lang, actual, expected);
            count++;
        }
        // This isolated XML fixture goes through the actual TMX object parser.
        Element group = DocumentBuilderFactory.newInstance().newDocumentBuilder()
            .parse(Paths.get(args[1]).toFile()).getDocumentElement();
        Class<?> mapType = Class.forName("com.corrodinggames.rts.game.b.b");
        Class<?> groupType = Class.forName("com.corrodinggames.rts.game.b.i");
        Object objects = groupType.getConstructor(Element.class, mapType).newInstance(group, mapType.getConstructor().newInstance());
        String[] keys = {"introText", "globalMessage", "text"};
        String[] locales = {"zh", "en", "", "fr"};
        for (Object object : (List<?>)groupType.getField("c").get(objects)) {
            for (String key : keys) {
                if (object.getClass().getMethod("b", String.class).invoke(object, key) == null) continue;
                for (String lang : locales) {
                    locale(lang);
                    bb text = (bb)object.getClass().getMethod("a", String.class, bb.class).invoke(object, key, null);
                    expect("map:" + key, lang, text.b(),
                        lang.equals("zh") ? "地图文本" : "Map text");
                    count++;
                }
            }
        }
        System.out.println("PASS: " + count + " native locale checks (zh/en/empty/fr), including all announcements and three map text types");
    }
}
