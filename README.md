# Power Punch Boxing Game 🥊

A modern boxing game with force sensors, real-time scoring, MongoDB-powered leaderboards, and an enhanced interactive UI!

## Features ✨

### Enhanced UI & User Experience:

- **Modern Interactive Interface**: Click-based navigation with hover effects
- **"New Player" Button**: Quick user switching after each punch
- **Enhanced Punch Results**: Beautiful result cards with achievement notifications
- **Mouse & Keyboard Support**: Full interaction with both input methods
- **Gradient Backgrounds**: Dynamic visual appeal with modern design
- **Card-Based Layout**: Professional interface with shadows and rounded corners

### MongoDB Integration Features:

- **Username Entry System**: Players can enter their name before playing
- **Score Storage**: All scores are stored in MongoDB with timestamps
- **Enhanced Leaderboard**: Top 10 scores with medals (🥇🥈🥉) and color-coded rankings
- **User High Scores**: Track individual player's best performances
- **Real-time Updates**: Immediate leaderboard updates after each punch

### Game Features:

- Real-time force sensor integration via Arduino
- Dynamic scoring based on punch strength
- Audio feedback with insults/praises
- Visual feedback with character images (Barbie for weak punches, Cena for strong ones)
- Demo Mode with keyboard controls (SPACE, 1, 2, 3)
- Responsive UI that scales to different screen sizes

## Requirements 📋

### Hardware:

- Arduino with force sensors (FSR)
- USB connection to computer

### Software:

- Python 3.7+
- MongoDB Atlas (Cloud Database) - **Already configured!**
- Required Python packages (see requirements.txt)

## Installation 🚀

1. **Clone or download the project files**

2. **Database Setup - MongoDB Atlas:**

   The game is already configured to use MongoDB Atlas (cloud database).
   No local MongoDB installation required!

   The game will automatically connect to the cloud database at:

   - **Cluster**: boxing.gd64oey.mongodb.net
   - **Database**: boxing_game
   - **Collection**: scores

3. **Set up Python environment:**

   ```bash
   # Create virtual environment
   python3 -m venv venv

   # Activate virtual environment
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\\Scripts\\activate  # On Windows

   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Test MongoDB setup:**

   ```bash
   python setup_mongodb.py
   ```

5. **Demo the features:**
   ```bash
   python demo_features.py
   ```

## How to Play 🎮

1. **Start the game:**

   ```bash
   source venv/bin/activate
   python boxing.py
   ```

2. **Enter your username** when prompted

3. **Navigation:**

   - Type your username and press `ENTER` to start
   - Press `L` to view the leaderboard
   - Press `U` during gameplay to change user
   - Press `B` or `ESC` to go back from leaderboard

4. **Punch the sensor!** The game will:
   - Display your score
   - Play audio feedback
   - Show character images based on performance
   - Store your score to the database
   - Update high scores if you beat records

## Scoring System 🎯

- **< 650**: Weak punch (Barbie appears with insults)
- **650-865**: Good punch (Barbie appears with encouragement)
- **> 865**: Powerful punch! (John Cena appears with praise)

## Database Structure 🗄️

The MongoDB database (`boxing_game`) contains a `scores` collection with documents:

```json
{
  "_id": "ObjectId",
  "username": "player_name",
  "score": 850,
  "timestamp": "2025-01-11T..."
}
```

## Game Controls 🕹️

### Mouse Controls (NEW!):

- **Click any button**: Navigate through the interface
- **Hover effects**: Buttons light up when hovered
- **"New Player" button**: Quick user switching available on all screens
- **"Leaderboard" button**: Instant access to top scores
- **"Punch Again" button**: Continue with current user

### Keyboard Controls:

#### Username Input Screen:

- **Type**: Enter your username
- **ENTER**: Start playing
- **L**: View leaderboard
- **Backspace**: Delete characters

#### Game Screen:

- **L**: View leaderboard
- **U**: Change username
- **SPACE**: Random punch (Demo mode)
- **1**: Weak punch (Demo mode)
- **2**: Medium punch (Demo mode)
- **3**: Strong punch (Demo mode)

#### Punch Result Screen (NEW!):

- **SPACE**: Return to game for another punch
- **L**: View leaderboard
- **U**: Change username

#### Leaderboard Screen:

- **B** or **ESC**: Go back

### Demo Mode (Arduino not connected):

- **SPACE**: Simulate random punch (650-1000)
- **1**: Simulate weak punch (600)
- **2**: Simulate medium punch (750)
- **3**: Simulate strong punch (900)

## Files Structure 📁

```
Power-Punch/
├── boxing.py              # Main game file with MongoDB integration
├── requirements.txt       # Python dependencies
├── setup_mongodb.py      # MongoDB setup and testing script
├── demo_features.py      # Feature demonstration script
├── high_scores.json      # Local backup for high scores
├── images/               # Game images
│   ├── bg.png           # Background image
│   ├── barbie.png       # Weak punch character
│   └── cenaa.png        # Strong punch character
├── *.mp3                # Audio files for feedback
└── boxing/              # Arduino code
    └── boxing.ino       # Arduino sensor code
```

## Troubleshooting 🔧

### MongoDB Issues:

- **Atlas connection failed**: Check your internet connection - the game needs internet to connect to MongoDB Atlas
- **Fallback to local**: If Atlas fails, the game will try local MongoDB automatically
- **No database connection**: Run `python setup_mongodb.py` to test the connection
- **Timeout errors**: Check your firewall settings - MongoDB Atlas uses port 27017

### Game Issues:

- **Serial connection error**: Check Arduino USB connection and port
- **Images not loading**: Verify image files are in the `images/` directory
- **Audio not playing**: Check audio files and pygame mixer initialization

### Import Errors:

- Make sure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

## Arduino Setup ⚡

The game expects serial data in this format:

```
FSR1: 500, FSR2: 600, Total: 1100
```

Make sure your Arduino code sends data in this format via serial connection.

## Contributing 🤝

Feel free to contribute improvements:

- Add more characters and audio clips
- Implement tournament modes
- Add difficulty levels
- Create web-based leaderboards
- Add data analytics and charts

## License 📄

This project is for educational and entertainment purposes.

---

**Ready to become the champion? Start punching! 🥊💪**
