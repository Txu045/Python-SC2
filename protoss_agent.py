import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.data import Alert
import random


class PyAgent(sc2.BotAI):
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAXWORKERSPERBASE = 22
        self.MAXWORKERS = 80
        self.MASSPYLONFLAG = False

    async def on_step(self, iteration):
        self.iteration = iteration

        # Eco building logic
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()

        # Military building logic
        await self.build_gateways()
        await self.build_cyberneticscores()
        await self.build_stargates()
        await self.build_roboticsfacilities()

        # Expand logic
        await self.expand()

        # Military unit logic
        await self.build_zealots()
        await self.build_stalkers()
        await self.build_voidrays()
        await self.build_immortals()

        # attack logic
        await self.attack()

    # basic logic for deciding if economy can support additional production buildings
    def assess_build_limit(self, costMinerals, costVespene):
        if ((self.minerals - costMinerals) > (costMinerals * 2)) and (
                (self.minerals - costVespene) > (costVespene * 2)):
            return True
        return False

    def calc_max_bases(self):
        return self.iteration / (self.ITERATIONS_PER_MINUTE * 2)

    # basic logic for deciding who to attack and how to defend
    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def build_workers(self):
        for nexus in self.units(UnitTypeId.NEXUS).ready.idle:
            if self.can_afford(UnitTypeId.PROBE) and self.units(UnitTypeId.PROBE).amount < \
                    (self.MAXWORKERSPERBASE * self.units(UnitTypeId.NEXUS).amount) and \
                    (self.units(UnitTypeId.PROBE).amount < self.MAXWORKERS):
                await self.do(nexus.train(UnitTypeId.PROBE))

    async def build_pylons(self):
        # logic causes mass pylons to be placed
        # if (self.supply_left < 1) and (self.supply_used < 200):
        #    nexuses = self.units(UnitTypeId.NEXUS).ready
        #    if nexuses.exists:
        #        if self.can_afford(UnitTypeId.PYLON):
        #            await self.build(UnitTypeId.PYLON, near=nexuses.first)
        if self.supply_used < 200:
            if (self.supply_left < 5) and not (self.already_pending(UnitTypeId.PYLON)):
                nexuses = self.units(UnitTypeId.NEXUS).ready
                if nexuses.exists:
                    if self.can_afford(UnitTypeId.PYLON):
                        await self.build(UnitTypeId.PYLON, near=nexuses.first, max_distance=30)
            if self.supply_left < 1 and self.assess_build_limit(200, 0):
                nexuses = self.units(UnitTypeId.NEXUS).ready
                if nexuses.exists:
                    if self.can_afford(UnitTypeId.PYLON):
                        await self.build(UnitTypeId.PYLON, near=nexuses.first, max_distance=30)

    async def build_assimilators(self):
        for nexus in self.units(UnitTypeId.NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vespene in vespenes:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(UnitTypeId.ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(UnitTypeId.ASSIMILATOR, vespene))

    async def expand(self):
        if self.units(UnitTypeId.NEXUS).amount <= self.calc_max_bases() and self.can_afford(UnitTypeId.NEXUS) \
                and not self.already_pending(UnitTypeId.NEXUS) and not self.alert(Alert.UnitUnderAttack):
            await self.expand_now()

    async def build_gateways(self):
        if self.units(UnitTypeId.PYLON).ready.exists:
            pylon = self.units(UnitTypeId.PYLON).ready.random
            canBuild = self.assess_build_limit(150, 0)
            if canBuild and not self.already_pending(UnitTypeId.GATEWAY):
                await self.build(UnitTypeId.GATEWAY, near=pylon)

    async def build_cyberneticscores(self):
        if self.units(UnitTypeId.PYLON).ready.exists:
            pylon = self.units(UnitTypeId.PYLON).ready.random
            if self.units(UnitTypeId.GATEWAY).ready.exists and not self.units(UnitTypeId.CYBERNETICSCORE).ready.exists:
                if self.can_afford(UnitTypeId.CYBERNETICSCORE) and not \
                        self.already_pending(UnitTypeId.CYBERNETICSCORE):
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)

    async def build_stargates(self):
        if self.units(UnitTypeId.PYLON).ready.exists:
            pylon = self.units(UnitTypeId.PYLON).ready.random
            canBuild = self.assess_build_limit(150, 50)
            if canBuild and not self.already_pending(UnitTypeId.STARGATE) and \
                    self.units(UnitTypeId.CYBERNETICSCORE).ready.exists:
                await self.build(UnitTypeId.STARGATE, near=pylon)

    async def build_roboticsfacilities(self):
        if self.units(UnitTypeId.PYLON).ready.exists:
            pylon = self.units(UnitTypeId.PYLON).ready.random
            canBuild = self.assess_build_limit(150, 150)
            if canBuild and not self.already_pending(UnitTypeId.ROBOTICSFACILITY) and \
                    self.units(UnitTypeId.CYBERNETICSCORE).ready.exists:
                await self.build(UnitTypeId.ROBOTICSFACILITY, near=pylon)

    async def build_zealots(self):
        for gateways in self.units(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.ZEALOT) and self.supply_left > 2 and self.units(UnitTypeId.NEXUS).amount > 1:
                await self.do(gateways.train(UnitTypeId.ZEALOT))

    async def build_stalkers(self):
        for gateways in self.units(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.STALKER) and self.supply_left > 2 and \
                    self.units(UnitTypeId.CYBERNETICSCORE).exists and self.units(UnitTypeId.NEXUS).amount > 1:
                await self.do(gateways.train(UnitTypeId.STALKER))

    async def build_voidrays(self):
        for stargates in self.units(UnitTypeId.STARGATE).ready.idle:
            if self.can_afford(UnitTypeId.VOIDRAY) and self.supply_left > 3 and \
                    self.units(UnitTypeId.STARGATE).exists and self.units(UnitTypeId.NEXUS).amount > 2:
                await self.do(stargates.train(UnitTypeId.VOIDRAY))

    async def build_immortals(self):
        for roboticsfacilities in self.units(UnitTypeId.ROBOTICSFACILITY).ready.idle:
            if self.can_afford(UnitTypeId.IMMORTAL) and self.supply_left > 3 and \
                    self.units(UnitTypeId.ROBOTICSFACILITY).exists and self.units(UnitTypeId.NEXUS).amount > 2:
                await self.do(roboticsfacilities.train(UnitTypeId.IMMORTAL))

    async def attack(self):
        # {UNIT: [n to attacks, n to defend]}
        aggressive_units = {UnitTypeId.ZEALOT: [15, 4, 7],
                            UnitTypeId.STALKER: [10, 2, 7],
                            UnitTypeId.VOIDRAY: [10, 1, 4],
                            UnitTypeId.IMMORTAL: [10, 1, 4]}

        for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > \
                    aggressive_units[UNIT][1]:
                for UNIT in aggressive_units:
                    for u in self.units(UNIT).idle:
                        await self.do(u.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for u in self.units(UNIT).idle:
                        await self.do(u.attack(random.choice(self.known_enemy_units)))

            elif self.units(UNIT).amount > aggressive_units[UNIT][2]:
                for u in self.units(UNIT).ready:
                    await self.do(u.attack(self.start_location))


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, PyAgent()),
    Computer(Race.Terran, Difficulty.Hard)
], realtime=False)
