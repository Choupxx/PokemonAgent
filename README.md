# PokemonAgent
Artificial Intelligence Fundamentals project for the a.y. 2024/2025.
- **Group name:** POKEMON-BATTLES
- **Group members:** [Pan Zhang](https://github.com/Choupoo)

## How to run the project
### Configuring a Pokémon Showdown Server
hosting a private server is advisable for training agents.
* Install Node.js v10+.
* Clone the Pokémon Showdown repository and set it up:
```bash
git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown
npm install
cp config/config-example.js config/config.js
node pokemon-showdown start --no-security
```
* The server will be running at `localhost:8000`.

### Running the agents
* Clone this repository and install the requirements:
```bash     
git clone https://github.com/Choupxx/PokemonAgent
cd PokemonAgent
pip install -r requirements.txt
```
* Run the agents:
```bash 
python main.py
```