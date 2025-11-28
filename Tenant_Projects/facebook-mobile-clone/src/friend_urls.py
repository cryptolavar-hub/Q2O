import express, { Request, Response } from 'express';
import http from 'http';
import { Server } from 'socket.io';
import mongoose from 'mongoose';
import jwt from 'jsonwebtoken';
import { body, validationResult } from 'express-validator';
import { createLogger, transports, format } from 'winston';

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret';

const logger = createLogger({
  level: 'info',
  format: format.combine(format.timestamp(), format.json()),
  transports: [new transports.Console()],
});

mongoose.connect('mongodb://localhost:27017/chat', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

const messageSchema = new mongoose.Schema({
  username: String,
  message: String,
  timestamp: { type: Date, default: Date.now },
});

const Message = mongoose.model('Message', messageSchema);

interface User {
  username: string;
}

const authenticateJWT = (req: Request, res: Response, next: () => void) => {
  const token = req.header('Authorization')?.split(' ')[1];
  if (!token) {
    return res.sendStatus(403);
  }
  jwt.verify(token, JWT_SECRET, (err: any, user: User) => {
    if (err) {
      return res.sendStatus(403);
    }
    req.user = user;
    next();
  });
};

app.use(express.json());

app.post('/login', 
  body('username').isString().notEmpty(),
  (req: Request, res: Response) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    
    const { username } = req.body;
    const token = jwt.sign({ username }, JWT_SECRET);
    logger.info(`User logged in: ${username}`);
    res.json({ token });
  }
);

io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  jwt.verify(token, JWT_SECRET, (err: any, user: User) => {
    if (err) {
      return next(new Error('Authentication error'));
    }
    socket.user = user;
    next();
  });
});

io.on('connection', (socket) => {
  logger.info(`User connected: ${socket.user.username}`);

  socket.on('sendMessage', async (message: string) => {
    try {
      const newMessage = new Message({ username: socket.user.username, message });
      await newMessage.save();
      io.emit('message', newMessage);
      logger.info(`Message sent: ${message}`);
    } catch (error) {
      logger.error(`Error sending message: ${error}`);
    }
  });

  socket.on('disconnect', () => {
    logger.info(`User disconnected: ${socket.user.username}`);
  });
});

server.listen(PORT, () => {
  logger.info(`Server is running on port ${PORT}`);
});