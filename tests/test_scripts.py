"""Testes dos scripts sem rede, sem Flow e sem ffmpeg: python -m unittest discover tests."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import frames
import gflow_cena
import montar


def saida_gflow(dados: dict) -> str:
    return "log antes\n" + json.dumps(dados, indent=2) + "\nfim\n"


class GflowCena(unittest.TestCase):
    def test_video_ok_devolve_media_id_e_arquivo(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp4") as mp4:
            dados = {"status": "ok", "succeeded": True, "media_id": "m1", "local_path": mp4.name}
            r = gflow_cena.resultado(0, saida_gflow(dados), "", video=True)
        self.assertEqual((r["ok"], r["media_id"], r["creditos"]), (True, "m1", 12))

    def test_video_sem_arquivo_e_indeterminado(self) -> None:
        dados = {"status": "ok", "succeeded": True, "media_id": "m2", "local_path": None}
        r = gflow_cena.resultado(0, saida_gflow(dados), "", video=True)
        self.assertFalse(r["ok"])
        self.assertTrue(r["pode_ter_cobrado"])
        self.assertEqual(r["media_id"], "m2")

    def test_recusa_de_conteudo_nao_cobra(self) -> None:
        dados = {"status": "fail", "problem": {"detail": "policy"}}
        r = gflow_cena.resultado(5, saida_gflow(dados), "", video=True)
        self.assertEqual((r["ok"], r["pode_ter_cobrado"], r["erro"]), (False, False, "policy"))

    def test_sem_personagem_nao_manda_reference_entity(self) -> None:
        ns = type("A", (), {"acao": "video", "personagem_id": None, "personagem_nome": "",
                            "perfil": "p", "saida": "s", "ref": ["f.jpg"], "projeto": "x",
                            "prompt": "oi"})()  # fmt: skip
        cmd = gflow_cena.comando(ns)
        self.assertNotIn("--reference-entity", cmd)
        self.assertEqual(cmd[cmd.index("--duration") + 1], "8")

    def test_prompt_imagem_cita_referencias_inline(self) -> None:
        ref = gflow_cena.nome_ref("cenas/01/quadro.jpg")
        self.assertEqual(ref, "quadro")
        t = gflow_cena.prompt_imagem(ref, "a sunlit kitchen, white counter", "a man", "Ana")
        self.assertTrue(t.startswith("Keep the @quadro reference image's exact setting, background,"
                                     " lighting, camera framing, composition and props: a sunlit kitchen"))
        self.assertIn("Replace ONLY the person with a man from the character @Ana.", t)

    def test_prompt_video_cita_personagem_cena_e_cenario(self) -> None:
        t = gflow_cena.prompt_video("imagem", "a sunlit kitchen", "A man", "Ana", "He nods.",
                                    'diga "oi" @fulano', "warm voice")  # fmt: skip
        self.assertIn("A man from the character @Ana.", t)
        self.assertIn("Same setting as the reference scene image @imagem: a sunlit kitchen; keep this"
                      " background, never the background of the character @Ana reference photos.", t)
        self.assertIn("He says to the camera: \"diga 'oi' fulano\" Voice: warm voice.", t)
        self.assertTrue(gflow_cena.prompt_video("i", "c", "A", "N", "", "", "v").endswith("No speech."))


class Config(unittest.TestCase):
    def test_ambiente_sobrescreve_arquivo(self) -> None:
        import os
        from unittest import mock

        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "config.json"
            arq.write_text(json.dumps({"perfil": "a", "projeto": "p1", "personagem_id": ""}))
            with mock.patch.dict(os.environ, {"GFLOW_PROJETO": "p2"}, clear=False):
                os.environ.pop("GFLOW_PERFIL", None)
                c = gflow_cena.carregar_config(arq)
        self.assertEqual((c["perfil"], c["projeto"]), ("a", "p2"))
        self.assertNotIn("personagem_id", c)

    def test_sem_projeto_da_erro(self) -> None:
        from unittest import mock

        with mock.patch.object(gflow_cena, "carregar_config", return_value={}):
            with self.assertRaises(SystemExit):
                gflow_cena.main(["video", "--prompt", "x", "--saida", "s", "--ref", "f.jpg", "--seco"])


class Montar(unittest.TestCase):
    def test_srt_reparte_o_tempo_e_mantem_as_palavras(self) -> None:
        texto = montar.blocos_srt([(0.0, 4.0, "um dois três quatro"), (4.0, 6.0, "")], 3, True)
        self.assertIn("00:00:00,000 --> ", texto)
        self.assertIn("UM DOIS TRÊS", texto)
        self.assertTrue(texto.rstrip().endswith("QUATRO"))
        self.assertIn("--> 00:00:04,000", texto)


class Frames(unittest.TestCase):
    def test_instantes_no_meio_das_partes(self) -> None:
        self.assertEqual(frames.instantes(10.0, 4), [1.25, 3.75, 6.25, 8.75])


if __name__ == "__main__":
    unittest.main()
