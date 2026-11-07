import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_build  # noqa: E402

BASE = "656064105c0e1fbd0a8f1d6e5f5d3a8b3c2e1f00"


def version(v, sha, broken=()):
    return {"version": v, "file": {"url": f"https://x/{v}", "sha256": sha},
            "broken_on": [{"horizon": b, "code": "E"} for b in broken]}


INDEX = {
    "projects": [
        {"id": "zoom", "kind": "native-mod", "versions": [version("2.1.0", "c" * 64), version("2.0.0", "b" * 64)]},
        {"id": "minimap", "kind": "native-mod", "versions": [version("1.4.0", "a" * 64)]},
        {"id": "broken", "kind": "native-mod", "versions": [version("1.0.0", "d" * 64, [BASE])]},
        {"id": "pack", "kind": "hmod", "versions": [version("1.0.0", "e" * 64)]},
    ],
    "revoked": [{"id": "zoom", "sha256": "c" * 64}],
}


class Key(unittest.TestCase):
    def test_the_key_is_the_launchers(self):
        # The same vector as horizon_release_sign::native_build's test: CI and the launcher name a build alike.
        mods = [("zoom", "2.0.0", "b" * 64), ("minimap", "1.4.0", "a" * 64)]
        self.assertEqual(native_build.request_key("x86_64-unknown-linux-gnu", BASE, mods),
                         "c07fffc296cf14c5c496a016a930f84b0d0ac028a63c667c2bdf47657788445d")

    def test_names(self):
        key = "0123456789abcdef" + "0" * 48
        self.assertEqual(native_build.release_tag(BASE), "native-builds-656064105c0e")
        self.assertEqual(native_build.archive(key, "aarch64-apple-darwin"),
                         "0123456789abcdef-aarch64-apple-darwin.tar.gz")
        self.assertEqual(native_build.signature(key, "aarch64-apple-darwin"),
                         "0123456789abcdef-aarch64-apple-darwin.sig")


class Pick(unittest.TestCase):
    def test_newest_unrevoked_version_unless_one_is_named(self):
        picked = native_build.pick(INDEX, ["zoom", "minimap@1.4.0"], BASE)
        self.assertEqual([(p["id"], p["version"]) for p in picked], [("zoom", "2.0.0"), ("minimap", "1.4.0")])

    def test_what_the_launcher_would_not_build_is_refused(self):
        for wanted in (["nothing"], ["pack"], ["zoom@2.1.0"], ["zoom@9"], ["broken"], ["zoom", "zoom@2.0.0"], []):
            with self.assertRaises(ValueError, msg=wanted):
                native_build.pick(INDEX, wanted, BASE)

    def test_broken_on_another_commit_still_builds(self):
        picked = native_build.pick(INDEX, ["broken"], "1" * 40)
        self.assertEqual(picked[0]["version"], "1.0.0")


class Sets(unittest.TestCase):
    def test_the_registrys_sets_are_native_mods_it_lists(self):
        lines = native_build.sets(native_build.ROOT / "prebuilt.toml")
        self.assertTrue(lines)
        official = {p.name for p in (native_build.ROOT / "native").iterdir() if (p / "compatibility.json").is_file()}
        for line in lines:
            for item in line.split():
                self.assertIn(item.partition("@")[0].replace("_", "-"), official, line)


if __name__ == "__main__":
    unittest.main()
