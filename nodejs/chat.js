var http = require('http'); 
var connect = require('connect');
var app = connect().use(function(req, res){res.setHeader("Access-Control-Allow-Origin", "localhost:8000");});
var server = http.createServer(app).listen(4000);
var io = require('socket.io').listen(server);
var cookie_reader = require('cookie');  
var querystring = require('querystring'); 
 
var redis = require('redis'); 
var sub = redis.createClient(); 

sub.subscribe('chat'); 

io.configure(function(){
    io.set('authorization', function(data, accept){
        if(data.headers.cookie){
            data.cookie = cookie_reader.parse(data.headers.cookie);
            return accept(null, true);
        }
        return accept('error', false);
    });
    io.set('log level', 1);
});

io.sockets.on('connection', function (socket) {
    socket.on('create', function(room) {
        socket.join(room);
      });

    socket.on('send_message', function (message) {
        var message1 = message.split("~");
        var chnl = message1[0];
        message1.shift();
        console.log(message);
        values = querystring.stringify({
            comment: message1.toString(),
            channel: chnl,
            sessionid: socket.handshake.cookie['sessionid']
        });
        
        var options = {
            host: 'localhost',
            port: 8000,
            path: '/node_api',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': values.length
            }
        };
        
        //Send message to Django server
        var req = http.request(options, function(res){
            res.setEncoding('utf8');
            
            //Print out error message
            res.on('data', function(message){
                if(message != 'Everything worked :)'){
                    console.log('Message: ' + message);
                }
            });
        });
        
        req.write(values);
        req.end();
    });
});

sub.on('message', function(channel, message){
    var message1 = message.split("~");
    var chnl = message1[0];
     message1.shift();
     console.log(message1);
    io.sockets.in(chnl).emit('message', message1.toString());
});