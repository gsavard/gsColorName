# Construire les installateurs

Tous les installateurs embarquent un exécutable **autonome** produit par PyInstaller (Python et Qt inclus) :
aucune installation de Python n'est nécessaire chez l'utilisateur.

Le numéro de version se trouve dans un seul fichier : **`version.py`**. Pensez aussi à mettre à jour
`packaging/windows/version_info.txt` et le `%changelog` de `packaging/linux/gscolorname.rpm.spec`.

## Linux : .deb et .rpm

Prérequis (Fedora) :
```bash
sudo dnf install python3 python3-pip rpm-build dpkg
```
Prérequis (Debian/Ubuntu) :
```bash
sudo apt install python3 python3-venv rpm dpkg-dev
```

Construction :
```bash
packaging/linux/build-packages.sh          # deb + rpm
packaging/linux/build-packages.sh rpm      # rpm seulement
REBUILD=0 packaging/linux/build-packages.sh deb   # réutilise dist/gscolorname existant
```

Étapes du script :
1. crée `.venv-build` et lance PyInstaller avec `packaging/gscolorname.spec`, ce qui produit `dist/gscolorname/` ;
2. prépare l'arborescence : `/opt/gscolorname`, le lien `/usr/bin/gscolorname`, le `.desktop` et les icônes hicolor ;
3. produit le `.deb` avec `dpkg-deb` et le `.rpm` avec `rpmbuild` (`AutoReqProv: no`, les dépendances système étant déclarées à la main).

> **Compatibilité glibc** : l'exécutable dépend de la glibc de la machine de construction. La CI construit
> sur Ubuntu 22.04 (glibc 2.35), ce qui assure la compatibilité avec Debian 12+, Ubuntu 22.04+ et Fedora 36+.

Vérifier un paquet :
```bash
dpkg -c dist/gscolorname_*.deb | head
rpm -qlp dist/gscolorname-*.rpm | grep -v _internal
rpm -qp --requires dist/gscolorname-*.rpm
```

## Windows : installateur .exe (Inno Setup)

Prérequis :
```powershell
winget install Python.Python.3.12
winget install JRSoftware.InnoSetup
```

Construction :
```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
```
Résultat : `dist\gsColorName-<version>-win64-setup.exe`.

Caractéristiques de l'installateur :
- installation par utilisateur par défaut (`PrivilegesRequired=lowest`), ou pour tous les utilisateurs via l'assistant ou `/ALLUSERS` ;
- interface en français et en anglais, raccourci dans le menu Démarrer et icône de bureau optionnelle ;
- options silencieuses standard d'Inno Setup (`/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/DIR=...`, `/LOG=...`).

Signature (optionnelle) : ajoutez `SignTool=...` dans `[Setup]` ou signez l'installateur après coup avec `signtool sign`.

## macOS : .app et .dmg

À lancer **sur un Mac** (PyInstaller ne fait pas de compilation croisée).
Prérequis : Python 3.10+ (python.org ou `brew install python`) et `xcode-select --install`.

```bash
packaging/macos/build-dmg.sh
```
Résultat : `dist/gsColorName.app` et `dist/gsColorName-<version>-macos-<arch>.dmg`.
L'architecture est celle du Mac de construction : un Mac Apple Silicon donne un paquet `arm64`, un Mac Intel un paquet `x86_64`.
La CI construit les deux (runners `macos-14` et `macos-15-intel`).

Signature :
- par défaut, signature **ad hoc** (`codesign -s -`), suffisante pour s'exécuter, mais Gatekeeper demande une confirmation ;
- avec un compte Apple Developer : `MAC_SIGN_IDENTITY="Developer ID Application: Nom (TEAMID)" packaging/macos/build-dmg.sh`,
  puis notarisation avec `xcrun notarytool submit dist/*.dmg --wait` et `xcrun stapler staple dist/*.dmg`.

Bundle : identifiant `ca.gsavard.gscolorname`, macOS 11 minimum, compatible Retina et mode sombre (voir `BUNDLE` dans `packaging/gscolorname.spec`).

## GitHub Actions

Le workflow `.github/workflows/release.yml` s'exécute :
- à chaque push sur `main` et pour chaque pull request : tests et construction des installateurs Windows, .deb, .rpm et .dmg (arm64 et x86_64) (récupérables dans les *Artifacts* du run) ;
- à chaque **tag `v*`** : en plus, création d'une **Release** GitHub avec les installateurs et `SHA256SUMS.txt`.

Publier une version :
```bash
# 1. mettre à jour version.py (+ version_info.txt, changelog RPM, CHANGELOG.md)
git commit -am "Version 1.1.0"
git tag v1.1.0
git push && git push --tags
```
