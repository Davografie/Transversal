<script setup lang="ts">
	import { ref } from 'vue'
	import { usePreferredColorScheme } from '@vueuse/core'
	import PP from '@/components/PP.vue'
	import Die from '@/components/Die.vue'
	import Traitset from '@/components/Traitset.vue'
	import type { Die as DieType, Traitset as TraitsetType } from '@/interfaces/Types'
	import { usePlayer } from '@/stores/Player'
	import { placeholder_d6 } from '@/composables/Die'
	import { useRoute, RouterLink } from 'vue-router'

	const player = usePlayer()
	const route = useRoute()

	const die: DieType = placeholder_d6
	const show_intro = ref(false)

	const show_mechanics = ref(false)
	const preferredColor = usePreferredColorScheme()
	const show_rolling = ref(false)
	const show_traitset = ref(false)
	const show_test = ref(false)
	const show_contest = ref(false)
	const show_heroic_success = ref(false)
	const show_ambient = ref(false)
	const show_sfx = ref(false)
	const show_dice = ref(false)
	const show_mutate_die = ref(false)
	const show_hitches = ref(false)

	const show_controls = ref(false)
	const show_character = ref(false)
	const show_navigating_locations = ref(false)
	const show_managing_codex = ref(false)
	const show_limits = ref(false)
	const show_architect = ref(false)
</script>

<template>
	<div class="wrapper" :class="preferredColor">

		<div id="intro_wrapper" :class="{ 'wrapper-active': show_intro }">
			<h1 @click="show_intro = !show_intro" :class="{ 'title-active': show_intro }">Transversal</h1>

			<div id="intro" class="rule" v-if="show_intro">
				<p>Welcome to Transversal! The game of the multiverse.</p>
				<p>You are tasked with defending reality against incursion and other threats.</p>
				<p>Transverse through universes, explore exotic locations, navigate complex webs of intrigue and danger, and harness resources and ideas.</p>
			</div>
		</div>

		<div id="controls_wrapper" :class="{ 'wrapper-active': show_controls }">
			<h1 @click="show_controls = !show_controls" :class="{ 'title-active': show_controls }">app controls & navigation</h1>
			<div id="controls" class="rule" v-if="show_controls">
				<p>You can often change something with a right-click or long-press.</p>
				<p>There's a high-contrast light theme and a sleek dark theme, change your browser or OS appearance to switch between themes.</p>
				<p>This app uses functional cookies to work, especially on phone.</p>
				<div id="character_select_wrapper" :class="{ 'wrapper-active': show_character }">
					<h2 @click="show_character = !show_character" :class="{ 'title-active': show_character }">character</h2>
					<div id="character-select-screen" class="rule" v-if="show_character">
						<b>pick/create a character</b>
						<ul>
							<li>Click <RouterLink :to="'/location/' + route.params.location_key + '/settings'">menu</RouterLink> in the top navigation bar, then <RouterLink :to="'/location/' + route.params.location_key + '/settings/characters'">characters</RouterLink>, here all characters are displayed.</li>
							<li>Click a character to play as that character, or click the empty character card with a + in it to create a new character.</li>
						</ul>
						<b>edit a character</b>
						<p>you can change the character's attributes by right-clicking or longpressing:</p>
						<ul>
							<li>portrait</li>
							<li>name</li>
							<li>description</li>
						</ul>
					</div>
				</div>
				<div id="traitset_wrapper" :class="{ 'wrapper-active': show_traitset }">
					<h2 @click="show_traitset = !show_traitset" :class="{ 'title-active': show_traitset }">traits</h2>
					<div id="trait-set" v-if="show_traitset">
						<div class="rule">
							<p>Playing TTRPG's is all about rolling dice.</p>
							<p>The traits declare which dice you should roll. Traits are grouped by traitset.</p>
						</div>
						<Traitset
							traitset_id="Traitsets/2"
							:entity_id="player.the_entity?.id ?? 'Entities/1'"
							location_key="104417835"
							visible
							expanded
							extensible
							tutorial />
						<div class="rule">
							<b>Traitset</b>
							<p>Your character has multiple traitsets.</p>
							<p>When playing, one traitset will be expanded and the rest will be collapsed.</p>
							<p>You are able to select traits from a traitset to add their rating to the dicepool.</p>
							<p>Traitset limits in the title bar determine how many traits you can add to the dicepool.</p>
							<p>You can see info and edit the traitset limit by right-clicking or longpressing the title.</p>
							<p>You can decrease and increase the traitset limit by pressing the ⊖ and ⊕ buttons.</p>
							<b>Trait</b>
							<p>Traits consist of:
								<ul>
									<li>
										<p class="li-name">name</p>
									</li>
									<li>
										<p class="li-name">statement</p>
										<p class="li-description">a description of max 7 words</p>
									</li>
									<li>
										<p class="li-name">notes</p>
										<p class="li-description">a longer description</p>
									</li>
									<li>
										<p class="li-name">rating</p>
										<p class="li-description">one or more dice</p>
										<p class="li-description">with a type of:</p>
										<ul>
											<li>
												<p class="li-name">empty</p>
												<p class="li-description">no dice</p>
											</li>
											<li>
												<p class="li-name">static</p>
												<p class="li-description">a constant value</p>
											</li>
											<li>
												<p class="li-name">challenge</p>
												<p class="li-description">represents a clock</p>
											</li>
											<li>
												<p class="li-name">resource</p>
												<p class="li-description">dice that represent the character's resources</p>
											</li>
										</ul>
									</li>
									<li>
										<p class="li-name">SFX's</p>
										<p class="li-description">an exception of the rules with: limit, cost, effect</p>
									</li>
									<li>
										<p class="li-name">sub-traits</p>
										<p class="li-description">traits within traits</p>
									</li>
									<li>
										<p class="li-name">location restriction</p>
										<p class="li-description">limits traits to specific locations</p>
									</li>
								</ul>
							</p>
							<p>You can edit a trait by right-clicking or longpressing it.</p>
							<p>Add traits by clicking the + button at the bottom of the traitset.</p>
						</div>
					</div>
				</div>
				<div id="navigating_locations_wrapper" :class="{ 'wrapper-active': show_navigating_locations }">
					<h2 @click="show_navigating_locations = !show_navigating_locations" :class="{ 'title-active': show_navigating_locations }">navigating locations</h2>
					<div id="navigating-locations" class="rule" v-if="show_navigating_locations">
						<p>In the panel on the left you can see the current location of your character.</p>
						<b>Parent location</b>
						<p>Navigate to the <b>parent location</b> by clicking its name at the top.</p>
						<b>Zones</b>
						<p>These are like sub-locations, are displayed inside and at the bottom of the current location.</p>
						<b>Transversable locations</b>
						<p>Beneath the current location are cards for <b>transversable locations</b>.</p>
						<p>Clicking a location card navigates to that location.</p>
					</div>
				</div>
				<div id="managing_codex_wrapper" :class="{ 'wrapper-active': show_managing_codex }">
					<h2 @click="show_managing_codex = !show_managing_codex" :class="{ 'title-active': show_managing_codex }">managing your contacts</h2>
					<div id="managing-codex" class="rule" v-if="show_managing_codex">
						<p>In the panel on the right you can see your contacts. Which is where you collect relationships.</p>
						<b>Adding</b>
						<p>You can add entities to your contacts by clicking the 🏷-icon on entity-cards or locations.</p>
						<b>Removing</b>
						<p>You can remove contacts by opening their entity-card and clicking 💔.</p>
					</div>
				</div>
				<div id="limits_wrapper" :class="{ 'wrapper-active': show_limits }">
					<h2 @click="show_limits = !show_limits" :class="{ 'title-active': show_limits }">de-/increase dicepool and traitset limits</h2>
					<div id="limits" class="rule" v-if="show_limits">
						<p>The dicepool and traitset title bars have buttons (⊖/⊕) you can click to decrease/increase their limits.</p>
					</div>
				</div>
				<div id="architect_wrapper" :class="{ 'wrapper-active': show_architect }">
					<h2 @click="show_architect = !show_architect" :class="{ 'title-active': show_architect }">architect</h2>
					<div id="architect" class="rule" v-if="show_architect">
						<p>As the architect of the game, you can create/update/delete entities (characters, locations, etc), traitsets, traits, and SFXs.</p>
						<b>changing PC starter traits</b>
						<p>Player characters are based on the archetype <i>default character</i> so if you want to edit something so all player characters start with a given trait, you can edit default character.</p>
						<b>Traversing as an NPC</b>
						<p>As the architect, you can change the location of the character you're currently playing by right-clicking another location and clicking traverse.</p>
						<b>change the default dicepool limit</b>
						<p>Change this in the main settings page. Set it to -1 for unlimited.</p>
					</div>
				</div>
			</div>
		</div>

		<div id="mechanics_wrapper" :class="{ 'wrapper-active': show_mechanics }">
			<h1 @click="show_mechanics = !show_mechanics" :class="{ 'title-active': show_mechanics }">the Cortex engine</h1>

			<div id="mechanics" v-if="show_mechanics">
				<div id="cortex-logo-wrapper">
					<img id="cortex-image" :src="'/img/CPC-' + preferredColor + '.png'" />
				</div>
				<div id="rolling_wrapper" :class="{ 'wrapper-active': show_rolling }">
					<h2 @click="show_rolling = !show_rolling" :class="{ 'title-active': show_rolling }">rolling</h2>
					<div id="rolling" class="rule" v-if="show_rolling">
						<div id="cortex-logo-spacer"></div>
						<b>Building a Dicepool</b>
						<p>From each traitset you may pick <u>1 trait</u><sup>1</sup> and add the trait's rating to the dicepool.</p>
						<b>Roll</b>
						<p>When finished building the dicepool, roll all dice in the pool.</p>
						<b>Result Dice</b>
						<p>Pick <u>2 dice</u><sup>12</sup>, their rolled numbers added together is your result.</p>
						<b>Effect Dice</b>
						<p>Pick <u>1 die</u><sup>12</sup>, the type of die is the effect.</p>
						<p><sup>1</sup><i><small>SFX's can increase how many you can pick</small></i></p>
						<p><sup>2</sup><i><small>you can't use hitches (rolled 1's)</small></i></p>
					</div>
				</div>
				<div id="test_wrapper" :class="{ 'wrapper-active': show_test }">
					<h2 @click="show_test = !show_test" :class="{ 'title-active': show_test }">tests</h2>
					<div id="test" class="rule" v-if="show_test">
						<p>Result-to-beat is rolled first.</p>
						<p>Default difficulty is <Die :die="die" /> <Die :die="die" /></p>
						<p>Add dice according to environment and character's complications.</p>
					</div>
				</div>
				<div id="contest_wrapper" :class="{ 'wrapper-active': show_contest }">
					<h2 @click="show_contest = !show_contest" :class="{ 'title-active': show_contest }">contests</h2>
					<div id="contest" class="rule" v-if="show_contest">
						<p>Challenger builds a dicepool and rolls first.</p>
						<p>Defender builds a dicepool and tries to beat the challenger's result.</p>
						<p><PP :amount="1" /> can be paid in order to push through, which means you can rebuild a dicepool and roll again.</p>
					</div>
				</div>
				<div id="heroic_success_wrapper" :class="{ 'wrapper-active': show_heroic_success }">
					<h2 @click="show_heroic_success = !show_heroic_success" :class="{ 'title-active': show_heroic_success }">heroic success</h2>
					<div id="heroic-success" class="rule" v-if="show_heroic_success">
						<p>A result of five or more over the competition is a heroic success.</p>
						<p>For each five above the competition, step up an effect die.</p>
					</div>
				</div>
				<div id="ambient_wrapper" :class="{ 'wrapper-active': show_ambient }">
					<h2 @click="show_ambient = !show_ambient" :class="{ 'title-active': show_ambient }">ambient threats</h2>
					<div id="ambient" class="rule" v-if="show_ambient">
						<p>In case of an ambient threat, a dicepool is preconstructed and persistent.</p>
						<p>Beating the dicepool decreases the ambient threat.</p>
						<p>Throwing hitches & botches increases the ambient threat.</p>
					</div>
				</div>
				<div id="sfx_wrapper" :class="{ 'wrapper-active': show_sfx }">
					<h2 @click="show_sfx = !show_sfx" :class="{ 'title-active': show_sfx }">special effects (SFX)</h2>
					<div id="sfx" class="rule" v-if="show_sfx">
						<p>A special effect can have a cost and/or a limit, and has an effect.</p>
						<p>Pay the cost, within the limits, to activate the effect.</p>
						<p>Most costs are expressed in <PP />.</p>
						<p>The default SFXs are:</p>
						<ul>
							<li>pay <PP /> to increase how many traits you can pick from the same traitset</li>
							<li>before rolling, pay <PP /> to increase the result limit of the dicepool</li>
							<li>pay <PP /> to step up an effect die</li>
							<li>buy a hitch from the game master for <PP /> to step down a complication</li>
							<li>after failing a contest, pay <PP /> to push through (i.e. build a new dicepool)</li>
						</ul>
					</div>
				</div>
				<div id="dice_wrapper" :class="{ 'wrapper-active': show_dice }">
					<h2 @click="show_dice = !show_dice" :class="{ 'title-active': show_dice }">dice</h2>
					<div id="dice" class="rule" v-if="show_dice">
						<div id="die-types">
							<table>
								<tr class="header">
									<td>dice</td>
									<td>effect</td>
									<td>trait rating</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: -5, rating: 'd12' }" /></td>
									<td>catastrophe</td>
									<td>debilitating</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: -4, rating: 'd10' }" /></td>
									<td>disaster</td>
									<td>threatening</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: -3, rating: 'd8' }" /></td>
									<td>major</td>
									<td>challenging</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: -2, rating: 'd6' }" /></td>
									<td>minor</td>
									<td>obstacle</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: -1, rating: 'd4' }" /></td>
									<td>irrelevant</td>
									<td>annoyance</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: 1, rating: 'd4' }" /></td>
									<td>partial</td>
									<td>novice</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: 2, rating: 'd6' }" /></td>
									<td>normal</td>
									<td>trained</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: 3, rating: 'd8' }" /></td>
									<td>great</td>
									<td>expert</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: 4, rating: 'd10' }" /></td>
									<td>astounding</td>
									<td>master</td>
								</tr>
								<tr>
									<td><Die :die="{ number_rating: 5, rating: 'd12' }" /></td>
									<td>epic</td>
									<td>visionary</td>
								</tr>
							</table>
						</div>
						<div id="mutate_die_wrapper" :class="{ 'wrapper-active': show_mutate_die }">
							<h3 @click="show_mutate_die = !show_mutate_die" :class="{ 'title-active': show_mutate_die }">mutate dice</h3>
							<div id="mutate_die" class="rule" v-if="show_mutate_die">
								<b>▼ Step down</b>
								<p>Decrease a die's type.</p>
								<p><Die :die="{ rating: 'd8' }" /> <span class="change-arrow"> ➟</span> <Die :die="{ rating: 'd6' }" /></p>
								<b>⇊ Split</b>
								<p>Replace a die with two of a lower type.</p>
								<p><Die :die="{ rating: 'd8' }" /> <span class="change-arrow"> ➟</span> <Die :die="{ rating: 'd6' }" /> <Die :die="{ rating: 'd6' }" /></p>
								<b>⧉ Double</b>
								<p>Add another die of the same type. Also counts for other multiplications, like triple or quadruple.</p>
								<p><Die :die="{ rating: 'd8' }" /> <span class="change-arrow"> ➟</span> <Die :die="{ rating: 'd8' }" /> <Die :die="{ rating: 'd8' }" /></p>
								<b>▲ Step up</b>
								<p>Increase a die's type.</p>
								<p><Die :die="{ rating: 'd8' }" /> <span class="change-arrow"> ➟</span> <Die :die="{ rating: 'd10' }" /></p>
							</div>
						</div>
						<div id="hitches_wrapper" :class="{ 'wrapper-active': show_hitches }">
							<h3 @click="show_hitches = !show_hitches" :class="{ 'title-active': show_hitches }">hitches & botches</h3>
							<div id="hitches" class="rule" v-if="show_hitches">
								<b>Hitch</b>
								<p>
									<Die :die="{ number_rating: 1, rating: 'd4', result: 1, isHitch: true }" in_pool />
									<Die :die="{ number_rating: 2, rating: 'd6', result: 1, isHitch: true }" in_pool />
									<Die :die="{ number_rating: 3, rating: 'd8', result: 1, isHitch: true }" in_pool />
									<Die :die="{ number_rating: 4, rating: 'd10', result: 1, isHitch: true }" in_pool />
									<Die :die="{ number_rating: 5, rating: 'd12', result: 1, isHitch: true }" in_pool />
								</p>
								<p>A hitch is rolling a 1 on a die.</p>
								<p>When a player rolls a hitch, the game master can buy that hitch by paying the player <PP :amount="1" />, this incurs a d6 complication, or steps up an existing complication, for the player character.</p>
								<p>When a player rolls multiple hitches in one dicepool, the game master can buy all for <PP :amount="1" />, but it will incur a larger complication.</p>
								<p>When the game master rolls a hitch, a player can buy that hitch from the game master for <PP :amount="1" />, by doing this the player can step down a complication.</p>
								<b>Botch</b>
								<p>A botch is rolling 1's on all dice in a dicepool. Shit hits the fan.</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<p id="hint" style="text-align: center" v-if="!show_intro && !show_mechanics && !show_controls">click a subject to learn more ⤴</p>
	</div>
</template>

<style scoped>
	.wrapper {
		background-color: var(--color-background-mute);
		padding: 1em 0 4em 0;
		.wrapper-active {
			border: 1px solid var(--color-highlight);
			margin: 1em;
		}
		h1, h2, h3 {
			cursor: pointer;
		}
		.title-active {
			border-bottom: 1px solid var(--color-highlight);
		}
		.rule {
			padding: .6em;
			text-align: justify;
			p {
				padding-left: 1em;
			}
			.li-name {
				font-weight: bold;
			}
		}
		#cortex-logo-wrapper {
			height: 0px;
			overflow: visible;
			position: relative;
			#cortex-image {
				width: 20%;
				position: absolute;
				top: 10px;
				right: 10px;
			}
		}
		#cortex-logo-spacer {
			float: right;
			height: 50px;
			width: 120px;
		}
		#hint {
			padding-top: 1em;
		}
		#die-types {
			display: flex;
			justify-content: space-evenly;
			table {
				text-align: center;
				tr {
					td {
						padding: 0 1em;
					}
				}
			}
		}
		.change-arrow {
			font-size: 3em;
		}
	}
</style>

<style>
.dark {
	.wrapper {
		.title-active {
			color: var(--color-highlight);
		}
	}
}
</style>
