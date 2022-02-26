const SCALE = 0.33;
var explosionImages = null;
var shellImage = null;
var hullImage = null;
var turretImage = null;
var barrelImage = null;
var trackImages = null;
var arena = null;
var lastUpdate = null;
var webSocket = null;

function openSocket() {
    var loc = window.location;
    var scheme = loc.protocol === "https:" ? "wss:" : "ws:";

    webSocket = new WebSocket(`${scheme}//${loc.host}/api/watch`);

    webSocket.onopen = function (event) {
        console.log("open websocket")
    };

    webSocket.onmessage = function (event) {
        arena = JSON.parse(event.data);
        window.requestAnimationFrame(draw);
    };

    webSocket.onclose = function (event) {
        window.setTimeout(openSocket, 1000);
    };
}

window.onload = function () {
    explosionImages = [
        document.getElementById("explosion0"),
        document.getElementById("explosion1"),
        document.getElementById("explosion2"),
        document.getElementById("explosion3"),
        document.getElementById("explosion4"),
        document.getElementById("explosion5"),
        document.getElementById("explosion6"),
        document.getElementById("explosion7")
    ];
    shellImage = document.getElementById("lightShell");
    hullImage = document.getElementById("hull1");
    turretImage = document.getElementById("gun1B");
    barrelImage = document.getElementById("gun1A");
    trackImages = [
        document.getElementById("track1A"),
        document.getElementById("track1B")
    ];
    openSocket();
}

function draw(timestamp) {
    if (timestamp == lastUpdate) {
        return;
    }
    lastUpdate = timestamp;

    var ctx = document.getElementById('canvas').getContext('2d');

    ctx.save();
    ctx.clearRect(0, 0, 1000, 1000);
    ctx.strokeStyle = 'black';
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, 1000, 1000);
    ctx.stroke();
    ctx.restore();

    arena.robots.forEach(robot => {
        const img = hullImage;
        const dx = robot.position.x;
        const dy = robot.position.y;
        const trackImgIndex = Math.round(timestamp * 3 * robot.velocity) % 2;

        ctx.save();
        ctx.translate(dx, dy);
        ctx.scale(SCALE, SCALE);

        // Labels
        const labely = hullImage.height * (dy < 500 ? 0.75 : -0.75);
        ctx.fillStyle = 'red';
        ctx.font = '50px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${robot.name} (${robot.health}%)`, 0, labely);

        // Draw the tracks+tank
        var trackImage = trackImages[trackImgIndex];
        ctx.rotate(Math.PI / 2 + robot.tank_angle / 180 * Math.PI);
        ctx.drawImage(trackImage, -img.width * 0.38, -trackImage.height / 2);
        ctx.drawImage(trackImage, +img.width * 0.38 - trackImage.width, -trackImage.height / 2);
        ctx.drawImage(img, -img.width / 2, -img.height / 2);

        ctx.restore();
    });

    // Draw turrets and barrels on top of neighbouring robots
    arena.robots.forEach(robot => {
        ctx.save();
        ctx.translate(robot.position.x, robot.position.y);
        ctx.scale(SCALE, SCALE);
        ctx.rotate(Math.PI / 2 + (robot.tank_angle + robot.turret_angle) / 180 * Math.PI);
        if (robot.fired) {
            ctx.translate(0, -4);
        }
        ctx.drawImage(turretImage, -turretImage.width / 2, -turretImage.height / 2);
        ctx.drawImage(barrelImage, -barrelImage.width / 2, -barrelImage.height / 2 - turretImage.height);
        ctx.restore();
    });

    arena.missiles.forEach(missile => {
        const missileScale = SCALE * .5 * (0.01 + 0.99 * missile.energy);
        if (!missile.exploding) {
            const img = shellImage;
            const dx = missile.position.x;
            const dy = missile.position.y;

            ctx.save();
            ctx.translate(dx, dy);
            ctx.scale(missileScale, missileScale)
            ctx.rotate(Math.PI / 2 + missile.angle / 180 * Math.PI);
            ctx.drawImage(img, - img.width / 2, - img.height / 2);
            ctx.restore();

        } else {
            const img = explosionImages[missile.explode_progress];
            const dx = missile.position.x
            const dy = missile.position.y
            ctx.save();
            ctx.translate(dx, dy);
            ctx.scale(missileScale, missileScale)
            ctx.drawImage(img, - img.width / 2, - img.height / 2);
            ctx.restore();
        }
    });

    if (arena.winner) {
        ctx.fillStyle = 'red';
        ctx.font = '50px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Winner ${arena.winner}!`, 500, 500);
    }
}
