"""kino-makon/tests/translit.test.ts asosidagi portlangan testlar."""

from app.services.translit import latinize, normalize_title


class TestLatinize:
    def test_kirill_harflarni_lotinga_otkazadi(self):
        assert latinize("Бойчечак") == "boychechak"
        assert latinize("Ассалом") == "assalom"

    def test_ozbek_kirill_belgilari_togri(self):
        assert latinize("ўғил") == "o'g'il"
        assert latinize("қалб") == "qalb"
        assert latinize("ҳаёт") == "hayot"

    def test_katta_harfni_kichiklashtiradi(self):
        assert latinize("O'zbekiston") == "o'zbekiston"


class TestNormalizeTitle:
    def test_okina_birlashtiradi_va_tinish_belgilarini_olib_tashlaydi(self):
        assert normalize_title("Bo'ychechak") == "boychechak"
        assert normalize_title("Bo`ychechak") == "boychechak"
        assert normalize_title("Boʻychechak") == "boychechak"
        assert normalize_title("Boychechak") == "boychechak"

    def test_kirill_va_lotin_variantlari_bir_xil_norma_beradi(self):
        assert normalize_title("Бойчечак") == "boychechak"
        assert normalize_title("Bo'ychechak") == "boychechak"

    def test_ortiqcha_boshliqlarni_siqadi(self):
        assert normalize_title("   Kino   nomi  ") == "kino nomi"

    def test_g_variantlari_bir_xil(self):
        assert normalize_title("G'ayrat") == "gayrat"
        assert normalize_title("Ғайрат") == "gayrat"

    def test_belgilar_raqamlar_aralashmasini_tozalaydi(self):
        assert normalize_title("Spider-Man 2!") == "spider man 2"

    def test_aksentlangan_harflarni_asosiy_harfga_yigadi(self):
        assert normalize_title("Émigré") == "emigre"
        assert normalize_title("À la recherche") == "a la recherche"
        assert normalize_title("Café") == "cafe"

    def test_kombinatsiyalovchi_diakritiklarni_olib_tashlaydi(self):
        assert normalize_title("émigre") == "emigre"
        assert normalize_title("òc") == "oc"

    def test_turkiy_harflarni_yigadi(self):
        assert normalize_title("Ğandım") == "gandim"
        assert normalize_title("Ĥikmat") == "hikmat"

    def test_aksent_fold_kirill_transkripsiyani_buzmaydi(self):
        assert normalize_title("Бойчечак") == "boychechak"
        assert normalize_title("Қўрғонтепа") == "qorgontepa"
