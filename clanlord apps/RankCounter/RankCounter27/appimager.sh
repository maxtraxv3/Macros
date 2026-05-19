#!/bin/bash
set -e

echo "==> Auto-detecting latest rcXX.py file"
PYFILE=$(ls rc*.py | sort -V | tail -n 1)

if [ -z "$PYFILE" ]; then
    echo "ERROR: No rcXX.py file found!"
    exit 1
fi

echo "==> Found Python file: $PYFILE"

# Extract version number (XX)
VERSION_NUM=$(echo "$PYFILE" | sed -E 's/rc([0-9]+)\.py/\1/')
APP="RC$VERSION_NUM"
BIN="rc$VERSION_NUM"
VERSION="$VERSION_NUM"

echo "==> Version detected: $VERSION"
echo "==> APP name: $APP"
echo "==> Binary name: $BIN"

echo "==> Cleaning old AppDir"
rm -rf $APP.AppDir
mkdir -p $APP.AppDir/usr/bin
mkdir -p $APP.AppDir/usr/share/applications
mkdir -p $APP.AppDir/usr/share/icons/hicolor/256x256/apps

echo "==> Copying binary"
cp dist/$BIN $APP.AppDir/usr/bin/

echo "==> Copying icon"
cp phoenix.png $APP.AppDir/usr/share/icons/hicolor/256x256/apps/$APP.png
cp phoenix.png $APP.AppDir/$APP.png

echo "==> Copying extra files"
cp phoenix.png $APP.AppDir/
cp rankmessages.txt $APP.AppDir/
cp trainers.txt $APP.AppDir/
cp specialphrases.txt $APP.AppDir/

echo "==> Generating .desktop file"
cat <<EOF > $APP.AppDir/usr/share/applications/$APP.desktop
[Desktop Entry]
Type=Application
Name=$APP
Exec=AppRun
Icon=$APP
Terminal=false
Categories=Utility;
EOF

chmod 644 $APP.AppDir/usr/share/applications/$APP.desktop

echo "==> Creating top-level .desktop file"
cp $APP.AppDir/usr/share/applications/$APP.desktop $APP.AppDir/$APP.desktop

echo "==> Verifying .desktop file exists"
find $APP.AppDir -name "*.desktop" -print

echo "==> Creating AppRun launcher"
cat <<EOF > $APP.AppDir/AppRun
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\$0")")"
export PATH="\$HERE/usr/bin:\$PATH"
exec "\$HERE/usr/bin/$BIN"
EOF

chmod +x $APP.AppDir/AppRun

echo "==> Building AppImage"
appimagetool $APP.AppDir ${APP}-${VERSION}-x86_64.AppImage

echo "==> Done!"
echo "Created: ${APP}-${VERSION}-x86_64.AppImage"
