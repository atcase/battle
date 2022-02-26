const SCALE = 1;
var backgroundImage = null;
var explosionImage = null;
var laserImage = null;
var hullImage = null;
var turretImage = null;
var galaxyImage = null;
var arena = null;
var lastUpdate = null;
var webSocket = null;
var stars = [];

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

const transpose = function (obj) {
    if (_.isNumber(obj) || _.isString(obj) || _.isNull(obj) || _.isBoolean(obj)) {
        return obj;
    }
    if (_.isArray(obj)) {
        return _.map(obj, transpose);
    }
    if (obj._t) {
        delete obj._t;
        const keys = _.keys(obj);
        const values = _.values(obj).map(transpose);
        return _.zip(...values).map(v => _.zipObject(keys, v));
    }
    return _.mapValues(obj, transpose);
}

window.onload = function () {
    laserImage = document.getElementById("laser");
    hullImage = document.getElementById("ship");
    turretImage = document.getElementById("turret");
    explosionImage = document.getElementById("explosion");
    galaxyImage = document.getElementById("galaxy");
    backgroundImage = document.getElementById("background");
    openSocket();
    for (var i=0; i<2000; i++) {
        stars.push(randomStar());
    }
}

function randomStar() {
    return {x: 4*Math.random() - 2, y: 4*Math.random() - 2, z: 10*Math.random()};
}

function draw(timestamp) {
    if (timestamp == lastUpdate) {
        return;
    }
    lastUpdate = timestamp;

    const arenaT = transpose(arena);
    const ctx = document.getElementById('canvas').getContext('2d');

    ctx.save();
    ctx.clearRect(0, 0, 1000, 1000);
    ctx.strokeStyle = 'black';
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, 1000, 1000);
    ctx.stroke();
    ctx.globalAlpha = 0.3;
    ctx.drawImage(backgroundImage, 0, 0, backgroundImage.width / 2, backgroundImage.height / 2, 0, 0, 1000, 1000);
    ctx.restore();
    
    ctx.save();
    ctx.translate(500, 500);
    
    ctx.save();
    ctx.scale(0.05, 0.05);
    ctx.drawImage(galaxyImage, -galaxyImage.width / 2, -galaxyImage.height / 2);
    ctx.restore();
    
    ctx.fillStyle = `white`;
    stars.forEach(star => {
        const size = (2 - star.z/10)/1000;
        ctx.save();
        ctx.globalAlpha = (10-star.z) / 10;
        ctx.scale(1000, 1000);
        ctx.fillRect(star.x / star.z, star.y / star.z, size, size);
        ctx.restore();
        star.z -= 0.01;
    });
    stars = stars.map((s) => s.z > 0 ? s : randomStar())
    ctx.restore();
    
    arenaT.robots.forEach(robot => {
        const img = hullImage;
        const dx = robot.position.x;
        const dy = robot.position.y;

        ctx.save();
        ctx.translate(dx, dy);
        ctx.scale(SCALE, SCALE);

        // Dead robots become ghosts
        if (robot.health <= 0) {
            ctx.globalAlpha = 0.5;
        }

        // Labels
        const labely = hullImage.height * (dy < 500 ? 0.75 : -0.75);
        ctx.fillStyle = 'red';
        ctx.font = '16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${robot.name} (${robot.health}%)`, 0, labely);

        // Draw the hull
        ctx.rotate(Math.PI / 2 + robot.hull_angle / 180 * Math.PI);
        ctx.drawImage(img, -img.width / 2, -img.height / 2);
        
        // Draw the turret
        const imgDim = turretImage.height;
        const idx = robot.firing_progress || 0;
        console.log(idx)
        ctx.rotate(robot.turret_angle / 180 * Math.PI);
        ctx.drawImage(turretImage, imgDim*idx, 0, imgDim, imgDim, -imgDim / 2, -imgDim / 2, imgDim, imgDim);
        // ctx.drawImage(turretImage, -turretImage.width / 2, -turretImage.height / 2);
        ctx.restore();
    });

    arenaT.missiles.forEach(missile => {
        const laserScale = SCALE * (0.1 + 0.9 * missile.energy / 5);
        if (!missile.exploding) {
            const img = laserImage;
            const imgDim = laserImage.height;
            const idx = Math.round(timestamp*5) % (img.width / imgDim);
            const dx = missile.position.x;
            const dy = missile.position.y;

            ctx.save();
            ctx.translate(dx, dy);
            ctx.scale(laserScale, laserScale)
            ctx.rotate(Math.PI / 2 + missile.angle / 180 * Math.PI);
            ctx.drawImage(img, imgDim*idx, 0, imgDim, imgDim, -imgDim / 2, -imgDim / 2, imgDim, imgDim);
            ctx.restore();

        } else {
            const img = explosionImage;
            const imgDim = explosionImage.height;
            const idx = missile.explode_progress;
            const dx = missile.position.x
            const dy = missile.position.y
            ctx.save();
            ctx.translate(dx, dy);
            ctx.scale(laserScale * 2, laserScale * 2)
            ctx.drawImage(img, imgDim*idx, 0, imgDim, imgDim, -imgDim / 2, -imgDim / 2, imgDim, imgDim);
            ctx.restore();
        }
    });

    if (arenaT.winner) {
        ctx.fillStyle = 'red';
        ctx.font = '16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`Winner ${arenaT.winner}!`, 500, 500);
    }
}
