'use strict';

let clipboard = null;
import('clipboardy').then(clipboardy => {
    clipboard = clipboardy.default;
});
const { windowManager } = require("node-window-manager");
var robot = require("robotjs");
var express = require('express');
var app = express();
var Server = require('http').Server;
var server = new Server(app);

server.listen(8080);
robot.setKeyboardDelay(1);

// __dirname is used here along with package.json.pkg.assets
// see https://github.com/zeit/pkg#config and
// https://github.com/zeit/pkg#snapshot-filesystem
app.use('/', express.static(__dirname + '/views'));

app.get('/', function (req, res) {
  res.sendFile(__dirname + '/views/index.html');
});

app.get('/app/signal/send/:name/:message', function (req, res) {
    openSignalContact(req.params.name);
    robot.keyTap("a", 'control');
    robot.keyTap('backspace');
    insertViaClipboard(req.params.message);
    robot.keyTap('enter');
    res.json(windowManager.getWindows());
});

app.get('/app/signal/open/:name?', function (req, res) {
    openSignalContact(req.params.name);
    res.json(null);
});

function openSignalContact(name) {
    let signalWindows = windowManager.getWindows().filter(w => w.path.toLowerCase().includes("signal"));
    let signalWindow = signalWindows.filter(w => w.getTitle().toLowerCase() === "signal")[0];
    signalWindow.restore();
    signalWindow.bringToTop();
    robot.keyTap("escape");
    robot.keyTap("n", "control");
    //robot.typeString(name);
    insertViaClipboard(name);
    robot.keyTap("tab");
    robot.keyTap("enter");
    robot.keyTap("t", ["control", "shift"]);
}

function insertViaClipboard(text) {
    console.log(clipboard);
    clipboard.writeSync(text);
    robot.keyTap("v", "control");
    clipboard.writeSync('');
}