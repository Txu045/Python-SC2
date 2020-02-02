import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.data import Alert
import random


class PyAgent(sc2.BotAI):
    async def on_step(self, iteration):

        # Eco building logic
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()

        # Military building logic
        await self.build_gateways()
        await self.build_cyberneticscores()

        # Expand logic
        await self.expand()

        # Military unit logic
        await self.build_zealots()
        await self.build_stalkers()

        # attack logic
        await self.attack()

    # basic logic for deciding if economy can support additional production buildings
    def assess_build_limit(self, costMinerals, costVespene):
        if ((self.minerals - costMinerals) > (costMinerals*2)) and ((self.minerals - costVespene) > (costVespene*2)):
            return True
        return False

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
                    self.units(UnitTypeId.NEXUS).amount*18:
                await self.do(nexus.train(UnitTypeId.PROBE))

    async def build_pylons(self):
        # logic causes mass pylons to be placed
        # if (self.supply_left < 1) and (self.supply_used < 200):
        #    nexuses = self.units(UnitTypeId.NEXUS).ready
        #    if nexuses.exists:
        #        if self.can_afford(UnitTypeId.PYLON):
        #            await self.build(UnitTypeId.PYLON, near=nexuses.first)
        if (self.supply_left < 5) and not (self.already_pending(UnitTypeId.PYLON) and (self.supply_used < 200)):
            nexuses = self.units(UnitTypeId.NEXUS).ready
            if nexuses.exists:
                if self.can_afford(UnitTypeId.PYLON):
                    await self.build(UnitTypeId.PYLON, near=nexuses.first)

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
        if self.units(UnitTypeId.NEXUS).amount < 3 and self.can_afford(UnitTypeId.NEXUS) \
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
                if not self.units(UnitTypeId.CYBERNETICSCORE):
                    if self.can_afford(UnitTypeId.CYBERNETICSCORE) and not \
                            self.already_pending(UnitTypeId.CYBERNETICSCORE):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)

    async def build_zealots(self):
        for gateways in self.units(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.ZEALOT) and self.supply_left > 2:
                await self.do(gateways.train(UnitTypeId.ZEALOT))

    async def build_stalkers(self):
        for gateways in self.units(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.STALKER) and self.supply_left > 2:
                await self.do(gateways.train(UnitTypeId.STALKER))

    async def attack(self):
        if self.units(UnitTypeId.ZEALOT).amount > 10 or self.units(UnitTypeId.ZEALOT).amount + \
                self.units(UnitTypeId.STALKER).amount > 15:
            for zealot in self.units(UnitTypeId.ZEALOT).idle:
                await self.do(zealot.attack(self.find_target(self.state)))
            for stalker in self.units(UnitTypeId.STALKER).idle:
                await self.do(stalker.attack(self.find_target(self.state)))

        elif self.units(UnitTypeId.ZEALOT).amount + self.units(UnitTypeId.STALKER).amount > 5:
            if len(self.known_enemy_units) > 0:
                for zealot in self.units(UnitTypeId.ZEALOT).idle:
                    await self.do(zealot.attack(random.choice(self.known_enemy_units)))
                for stalker in self.units(UnitTypeId.STALKER).idle:
                    await self.do(stalker.attack(random.choice(self.known_enemy_units)))


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, PyAgent()),
    Computer(Race.Terran, Difficulty.Medium)
], realtime=False)
