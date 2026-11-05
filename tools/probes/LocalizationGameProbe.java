// Observe RW 1.15's single-player victory/defeat flags without changing gameplay.
public class LocalizationGameProbe {
    public static void main(String[] args) throws Exception {
        Thread observer = new Thread(() -> {
            try {
                Class<?> engineType = Class.forName("com.corrodinggames.rts.gameFramework.l");
                boolean announced = false;
                while (true) {
                    Object engine = engineType.getMethod("B").invoke(null);
                    if (engine != null) {
                        boolean victory = engineType.getField("dq").getBoolean(engine);
                        boolean defeat = engineType.getField("dt").getBoolean(engine);
                        if (victory && !defeat && !announced) {
                            System.out.println("I18N_ENGINE_VICTORY");
                            announced = true;
                        }
                        if (!victory) announced = false;
                    }
                    Thread.sleep(100);
                }
            } catch (Exception error) {
                error.printStackTrace();
            }
        }, "i18n-victory-observer");
        observer.setDaemon(true);
        observer.start();
        Class.forName("com.corrodinggames.rts.java.Main").getMethod("main", String[].class).invoke(null, (Object)args);
    }
}
