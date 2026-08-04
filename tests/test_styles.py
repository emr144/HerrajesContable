import unittest
import styles


class TestEscaladoInterfaz(unittest.TestCase):
    def test_calcular_factor_escala_total_retorna_valor_valido(self):
        factor = styles.calcular_factor_escala_total()
        self.assertGreater(factor, 0)
        self.assertLessEqual(factor, 3.0)


if __name__ == "__main__":
    unittest.main()
