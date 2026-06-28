from lg_ompc.entities import Entity, EntityState
from lg_ompc.actions import ActionSpec, ActionDirection
from lg_ompc.environment import Environment

ADMIN = "admin"

def _servers(env):
    return [e for e in env.entities.values() if getattr(e, "kind", "") == "server"]

def _update_state(env, target, key, value):
    env.entity(target).state[key] = value

ISOLATE = ActionSpec(
    name="isolate",
    direction=ActionDirection.OUTGOING,
    precondition=lambda env, action: not env.entity(action.target).state["isolated"],
    effect=lambda env, action: _update_state(env, action.target, "isolated", True),
    enumerate_targets=lambda env, actor: [s.name for s in _servers(env) if not s.state["isolated"]]
)

RECONNECT = ActionSpec(
    name="reconnect",
    direction=ActionDirection.OUTGOING,
    precondition=lambda env, action: env.entity(action.target).state["isolated"],
    effect=lambda env, action: _update_state(env, action.target, "isolated", False),
    enumerate_targets=lambda env, actor: [s.name for s in _servers(env) if s.state["isolated"]]
)

CLEAN = ActionSpec(
    name="clean",
    direction=ActionDirection.OUTGOING,
    precondition=lambda env, action: env.entity(action.target).state["infected"],
    effect=lambda env, action: _update_state(env, action.target, "infected", False),
    enumerate_targets=lambda env, actor: [s.name for s in _servers(env) if s.state["infected"]]
)

class Admin(Entity):
    kind = "active_agent"
    def outgoing_actions(self): return [ISOLATE, RECONNECT, CLEAN]
    def incoming_actions(self): return []

class Server(Entity):
    kind = "server"
    def outgoing_actions(self): return []
    def incoming_actions(self): return []

class IncidentWorld(Environment):
    goal = (
        "Stop the infection from reaching the DB and Payment gateway at all costs! "
        "You can 'isolate' nodes to instantly stop the spread across their connections, "
        "but isolated nodes provide no business value. 'clean' infected nodes to cure them. "
        "'reconnect' clean isolated nodes to restore business value. "
        "Maximize the total value of clean, connected nodes."
    )

    def __init__(self, entities):
        super().__init__(entities)

    def servers(self):
        return [e for e in self.entities.values() if getattr(e, "kind", "") == "server"]

    def update(self):
        # Infection spreads unconditionally to all connected, non-isolated nodes
        newly_infected = set()
        for s in self.servers():
            if s.state["infected"] and not s.state["isolated"]:
                for nbr_name in s.state["connections"]:
                    nbr = self.entity(nbr_name)
                    if not nbr.state["isolated"]:
                        newly_infected.add(nbr_name)
        for name in newly_infected:
            self.entity(name).state["infected"] = True

    def compute_relations(self):
        # Already implicit in the connections array
        return []

    def is_terminal(self):
        # Mission complete when nothing is infected AND nothing is isolated
        return not any(s.state["infected"] for s in self.servers()) and \
               not any(s.state["isolated"] for s in self.servers())

def build_world():
    # Topology:
    # Internet? -> w1, w2, w3 -> switch -> db, payment
    # Infection starts at all 3 workers!
    db = Server("db", EntityState({"infected": False, "isolated": False, "value": 100, "connections": ["switch"]}))
    payment = Server("payment", EntityState({"infected": False, "isolated": False, "value": 50, "connections": ["switch"]}))
    
    # The switch is the critical bridge
    switch = Server("switch", EntityState({"infected": False, "isolated": False, "value": 5, "connections": ["w1", "w2", "w3", "db", "payment"]}))
    
    # The expendable compute pool
    w1 = Server("w1", EntityState({"infected": True, "isolated": False, "value": 10, "connections": ["switch"]}))
    w2 = Server("w2", EntityState({"infected": True, "isolated": False, "value": 10, "connections": ["switch"]}))
    w3 = Server("w3", EntityState({"infected": True, "isolated": False, "value": 10, "connections": ["switch"]}))
    
    admin = Admin(ADMIN, EntityState({}))

    return IncidentWorld([
        db, payment, switch,
        w1, w2, w3, admin
    ])
