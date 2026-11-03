Name:           gscolorname
Version:        @VERSION@
Release:        1%{?dist}
Summary:        Nom et codes d'une couleur (HEX, RGB, CMJN, Lab...), pipette et IA
License:        MIT
URL:            https://github.com/gsavard/gsColorName
Source0:        stage.tar.gz
AutoReqProv:    no
Requires:       glibc >= 2.31, libglvnd-egl, libglvnd-glx, libxkbcommon, libxkbcommon-x11, fontconfig, dbus-libs, xcb-util-cursor, xcb-util-wm, xcb-util-keysyms
Recommends:     xdg-desktop-portal

%global debug_package %{nil}
%global __strip /bin/true
%global __brp_check_rpaths %{nil}
%global _build_id_links none

%description
Application de bureau Qt : convertit une couleur dans plus de 20 formats, trouve son
nom parmi 32 000 noms (CIEDE2000), pipette ecran (Wayland/X11) et assistant IA via
LM Studio ou OpenRouter.

%prep
%build

%install
mkdir -p %{buildroot}
tar -C %{buildroot} -xzf %{SOURCE0}

%post
/usr/bin/update-desktop-database -q /usr/share/applications &>/dev/null || :
/usr/bin/gtk-update-icon-cache -q -t /usr/share/icons/hicolor &>/dev/null || :

%postun
/usr/bin/update-desktop-database -q /usr/share/applications &>/dev/null || :

%files
/opt/gscolorname
/usr/bin/gscolorname
/usr/share/applications/gscolorname.desktop
/usr/share/icons/hicolor/256x256/apps/gscolorname.png
/usr/share/icons/hicolor/scalable/apps/gscolorname.svg
%doc /usr/share/doc/gscolorname

%changelog
* Tue Nov 03 2026 gsavard - 1.0.0-1
- Premiere version : formats de couleur, noms, pipette, assistant IA
