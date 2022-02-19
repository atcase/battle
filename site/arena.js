const SCALE = 0.33;
var explosionImages = null;
var shellImage = null;
var hullImage = null;
var turretImage = null;
var barrelImage = null;
var trackImages = null;
var arena = null;

var webSocket = new WebSocket("ws://localhost:8000/api/watch");
console.log("Hello")
webSocket.onopen = function (event) {
    console.log("open websocket")
};
webSocket.onmessage = function (event) {
    // console.log("got event")
    // console.log(event)
    arena = JSON.parse(event.data);
    window.requestAnimationFrame(draw);
};

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
}

function draw(timestamp) {
    var ctx = document.getElementById('canvas').getContext('2d');

    ctx.save();
    ctx.clearRect(1, 1, 1000, 1000);
    ctx.strokeStyle = 'black';
    ctx.rect(0, 0, 1000, 1000);
    ctx.stroke();
    ctx.restore();


    arena.robots.forEach(robot => {
      const img = hullImage;
      const dx = robot.position.x * 1000;
      const dy = robot.position.y * 1000;
      const trackImgIndex = Math.round(timestamp * 5 * robot.velocity) % 2;
      
      ctx.save();
      ctx.translate(dx, dy);
      ctx.scale(SCALE, SCALE);
      
      // Draw the tank
      ctx.rotate(Math.PI / 2 + robot.tank_angle/180 * Math.PI);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);
      
      // Draw the tracks
      var trackImage = trackImages[trackImgIndex];
      ctx.drawImage(trackImage, -img.width * 0.3, -trackImage.height / 2);
      ctx.drawImage(trackImage, +img.width * 0.3 - trackImage.width, -trackImage.height / 2);

      // Draw the turret and barrel
      ctx.rotate(robot.turret_angle/180 * Math.PI);
      ctx.drawImage(turretImage, -turretImage.width / 2, -turretImage.height / 2);      
      ctx.drawImage(barrelImage, -barrelImage.width / 2, -barrelImage.height / 2 -turretImage.height );

      ctx.restore();
    });

    arena.missiles.forEach(missile => {
        if (!missile.exploding) {
          const img = shellImage;
          const dx = missile.position.x * 1000;
          const dy = missile.position.y * 1000;
          
          ctx.save();
          ctx.translate(dx, dy);
          ctx.scale(SCALE, SCALE)
          ctx.rotate(Math.PI / 2 + missile.angle/180 * Math.PI );
          ctx.drawImage(img, - img.width / 2, - img.height / 2);
          ctx.restore();
          
        } else {
          const img = explosionImages[missile.explode_progress];
          const dx = missile.position.x * 1000 ;
          const dy = missile.position.y * 1000 ;
          ctx.save();
          ctx.translate(dx, dy);
          ctx.scale(SCALE, SCALE)
          ctx.drawImage(img, - img.width / 2, - img.height / 2);
          ctx.restore();
        }
    });
}


function clock() {
    var now = new Date();
    var ctx = document.getElementById('canvas').getContext('2d');
    ctx.save();
    ctx.clearRect(0, 0, 150, 150);
    ctx.translate(75, 75);
    ctx.scale(0.4, 0.4);
    ctx.rotate(-Math.PI / 2);
    ctx.strokeStyle = 'black';
    ctx.fillStyle = 'white';
    ctx.lineWidth = 8;
    ctx.lineCap = 'round';
  
    // Hour marks
    ctx.save();
    for (var i = 0; i < 12; i++) {
      ctx.beginPath();
      ctx.rotate(Math.PI / 6);
      ctx.moveTo(100, 0);
      ctx.lineTo(120, 0);
      ctx.stroke();
    }
    ctx.restore();
  
    // Minute marks
    ctx.save();
    ctx.lineWidth = 5;
    for (i = 0; i < 60; i++) {
      if (i % 5!= 0) {
        ctx.beginPath();
        ctx.moveTo(117, 0);
        ctx.lineTo(120, 0);
        ctx.stroke();
      }
      ctx.rotate(Math.PI / 30);
    }
    ctx.restore();
  
    var sec = now.getSeconds();
    var min = now.getMinutes();
    var hr  = now.getHours();
    hr = hr >= 12 ? hr - 12 : hr;
  
    ctx.fillStyle = 'black';
  
    // write Hours
    ctx.save();
    ctx.rotate(hr * (Math.PI / 6) + (Math.PI / 360) * min + (Math.PI / 21600) *sec);
    ctx.lineWidth = 14;
    ctx.beginPath();
    ctx.moveTo(-20, 0);
    ctx.lineTo(80, 0);
    ctx.stroke();
    ctx.restore();
  
    // write Minutes
    ctx.save();
    ctx.rotate((Math.PI / 30) * min + (Math.PI / 1800) * sec);
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(-28, 0);
    ctx.lineTo(112, 0);
    ctx.stroke();
    ctx.restore();
  
    // Write seconds
    ctx.save();
    ctx.rotate(sec * Math.PI / 30);
    ctx.strokeStyle = '#D40000';
    ctx.fillStyle = '#D40000';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(-30, 0);
    ctx.lineTo(83, 0);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(0, 0, 10, 0, Math.PI * 2, true);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(95, 0, 10, 0, Math.PI * 2, true);
    ctx.stroke();
    ctx.fillStyle = 'rgba(0, 0, 0, 0)';
    ctx.arc(0, 0, 3, 0, Math.PI * 2, true);
    ctx.fill();
    ctx.restore();
  
    ctx.beginPath();
    ctx.lineWidth = 14;
    ctx.strokeStyle = '#325FA2';
    ctx.arc(0, 0, 142, 0, Math.PI * 2, true);
    ctx.stroke();
  
    ctx.restore();
  
    window.requestAnimationFrame(clock);
  }
  
//   window.requestAnimationFrame(clock);
  