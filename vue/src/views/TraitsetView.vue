<script setup lang="ts">
	import { ref, computed, watch } from 'vue'
	import type { Ref } from 'vue'
	import { useRoute } from 'vue-router'

	import { usePlayer } from '@/stores/Player'

	// import Trait from '@/components/Trait.vue'
	import TraitEdit from '@/components/TraitEdit.vue'
	import Die from '@/components/Die.vue'
	import DiePicker from '@/components/DiePicker.vue'
	import LocationSelector from '@/components/LocationSelector.vue'
	import ToggleButton from '@/components/ToggleButton.vue'
	import SFX from '@/components/SFX.vue'

	import { useTraitset } from '@/composables/Traitset'
	import { rating_types } from '@/composables/Trait'
	import { useSFXList } from '@/composables/SFXList'

	import type { Die as DieType, Trait as TraitType, SFX as SFXType } from '@/interfaces/Types'

	const props = defineProps<{
		traitset_key?: string
	}>()

	const route = useRoute()

	const player = usePlayer()

	const {
		traitset,
		set_traitset_id,
		retrieve_traitset,
		default_settings,
		mutate_traitset,
		retrieve_default_settings,
		mutate_default_settings,
		create_trait
	} = 
		useTraitset(undefined, "Traitsets/" + (props.traitset_key ?? route.params.id.toString()), undefined)

	const { sfx_list } = useSFXList()

	retrieve_traitset()
	retrieve_default_settings()

	const show_defaults: Ref<boolean> = ref(false)
	function toggle_defaults() {
		if(!show_defaults.value) {
			retrieve_default_settings()
			new_traitset_rating.value = default_settings.value?.rating ?? []
			new_traitset_rating_type.value = default_settings.value?.ratingType ?? rating_types[0]
			new_trait_default_sfxs.value = default_settings.value?.sfxs ?? []
		}
		show_defaults.value = !show_defaults.value
	}

	const show_trait_details: Ref<string[]> = ref([])
	function toggle_trait(trait: TraitType) {
		if(show_trait_details.value.includes(trait.id)) {
			show_trait_details.value.splice(show_trait_details.value.indexOf(trait.id), 1)
		}
		else {
			show_trait_details.value.push(trait.id)
		}
	}
	
	enum abled {
		ENABLED = 0,
		ENABLED_IMPLIED = 1,
		NEUTRAL = 2,
		DISABLED = 3,
		DISABLED_IMPLIED = 4
	}
	const ability = [
		{ abled: abled.ENABLED, name: "enabled", symbol: "✓" },
		{ abled: abled.ENABLED_IMPLIED, name: "implied enabled", symbol: "✓" },
		{ abled: abled.NEUTRAL, name: "neutral", symbol: "⚬" },
		{ abled: abled.DISABLED, name: "disabled", symbol: "✗" },
		{ abled: abled.DISABLED_IMPLIED, name: "implied disabled", symbol: "✗" },
	]

	// traitset settings
	const traitset_name: Ref<string> = ref(traitset.value.name ?? '')
	const traitset_explainer: Ref<string> = ref(traitset.value.explainer ?? '')
	const traitset_limit: Ref<number> = ref(traitset.value.limit ?? 1)
	const entity_types = ref<string[]>(traitset.value.entityTypes ?? [])
	const allows_duplicates = ref(false)
	const new_locations_enabled = ref<string[]>([])
	const new_locations_disabled = ref<string[]>([])
	const new_sfxs = ref<SFXType[]>(traitset.value.sfxs ?? [])
	const adding_sfx = ref(false)

	const pick_default_rating: Ref<boolean> = ref(false)

	const traitset_changed = computed(() => {
		return traitset_name.value != traitset.value.name
			|| traitset_explainer.value != traitset.value.explainer
			|| traitset_limit.value != traitset.value.limit
			|| entity_types.value != traitset.value.entityTypes
			|| allows_duplicates.value != traitset.value.duplicates
			|| !arraysEqual(new_sfxs.value.map(sfx => sfx.id), traitset.value.sfxs?.map(sfx => sfx.id) ?? [])
	})

	function arraysEqual(a: string[], b: string[]) {
		if (a.length != b.length) return false
		for(let i = 0; i < a.length; i++) {
			if (a[i] != b[i]) return false
		}
		return true
	}

	watch(traitset, (new_traitset) => {
		traitset_name.value = new_traitset.name ?? ''
		traitset_explainer.value = new_traitset.explainer ?? ''
		traitset_limit.value = new_traitset.limit ?? 1
		entity_types.value = new_traitset.entityTypes ?? []
		allows_duplicates.value = new_traitset.duplicates ?? false
		new_sfxs.value = new_traitset.sfxs ?? []
	})

	function add_sfx(sfx: SFXType) {
		if(!new_sfxs.value || new_sfxs.value.length == 0) new_sfxs.value = [sfx]
		else new_sfxs.value = [...new_sfxs.value, sfx]
		adding_sfx.value = false
	}

	function remove_sfx(sfx: SFXType) {
		new_sfxs.value = new_sfxs.value.filter(x => x.id != sfx.id)
	}

	function update_locations(locations_enabled: string[], locations_disabled: string[]) {
		console.log("enabled locations: ", locations_enabled, " disabled: ", locations_disabled)
		default_settings.value = { ...default_settings.value, locationsEnabled: locations_enabled, locationsDisabled: locations_disabled }
		mutate_default_settings({
			locationsEnabled: locations_enabled,
			locationsDisabled: locations_disabled
		})
	}

	// default settings
	const new_traitset_rating: Ref<DieType[]> = ref(traitset.value.defaultTraitSetting?.rating ?? default_settings.value?.rating ?? [])
	const new_traitset_rating_type: Ref<string> = ref(default_settings.value?.ratingType ?? rating_types[0])
	const new_trait_default_sfxs = ref<string[]>([])

	const new_trait_name: Ref<string> = ref("")

	function change_default_traitset_settings() {
		mutate_default_settings({
			ratingType: new_traitset_rating_type.value,
			rating: new_traitset_rating.value.map(d => d.number_rating),
			locationsEnabled: new_locations_enabled.value,
			locationsDisabled: new_locations_disabled.value,
			sfxs: new_trait_default_sfxs.value
		})
		setTimeout(() => retrieve_default_settings(), 200)
	}

	watch(default_settings, (new_default_settings) => {
		new_traitset_rating.value = new_default_settings?.rating ?? []
		new_traitset_rating_type.value = new_default_settings?.ratingType ?? rating_types[0]
		new_trait_default_sfxs.value = new_default_settings?.sfxsIds ?? []
		new_locations_enabled.value = new_default_settings?.locationsEnabled ?? []
		new_locations_disabled.value = new_default_settings?.locationsDisabled ?? []
	})

	function update_traitset() {
		mutate_traitset({
			name: traitset_name.value,
			explainer: traitset_explainer.value,
			entityTypes: entity_types.value,
			duplicates: allows_duplicates.value,
			limit: traitset_limit.value,
			sfxs: new_sfxs.value.map(sfx => sfx.id)
		})
		setTimeout(() => retrieve_traitset(), 200)
	}
	
	const show_default_rating = computed(() => {
		return pick_default_rating.value || new_traitset_rating.value?.length == 0
	})

	function increase_rating_type(rating_type: string) {
		// cycles through rating types to change trait rating type
		const rating_index: number = rating_types.findIndex(x => x == rating_type)
		return rating_types[(rating_index + 1) % rating_types.length]
	}

	function change_taitset_default_rating(dice: DieType[]) {
		new_traitset_rating.value = dice
		pick_default_rating.value = false
		change_default_traitset_settings()
	}
	const player_can_change_rating: Ref<boolean> = ref(false)
	const show_trait_default_sfx = ref<boolean>(false)
	function toggle_sfx(sfx_id: string) {
		console.log('toggling sfx: ', sfx_id)
		if(new_trait_default_sfxs.value.includes(sfx_id)) {
			const i = new_trait_default_sfxs.value.indexOf(sfx_id)
			new_trait_default_sfxs.value.splice(i, 1)
		}
		else {
			new_trait_default_sfxs.value = [...new_trait_default_sfxs.value, sfx_id]
		}
	}


	import useClipboard from 'vue-clipboard3'
	const { toClipboard } = useClipboard()
	const copy = async () => {
		try {
			await toClipboard(traitset.value.id)
			console.log('Copied to clipboard')
		} catch (e) {
			console.error(e)
		}
	}

	watch(() => props.traitset_key, (newKey) => {
		if(newKey) {
			set_traitset_id('Traitsets/' + newKey)
			retrieve_traitset()
		}
	})
</script>

<template>
	<div id="traitset-view">
		<input type="text" class="header" v-model="traitset_name" />
		<input type="button" class="button"
			v-if="traitset.name != traitset_name" value="rename"
			@click="mutate_traitset({'name': traitset_name})" />
		<input type="button" @click.stop="copy" class="copy-id button" title="copy trait id" value="#" />
		<h2>settings</h2>
		<div id="traitset-settings">
			<div>
				<h3>traitset settings</h3>
				<h4>explainer</h4>
				<textarea id="explainer" v-model="traitset_explainer" placeholder="Enter explainer"></textarea>
				<!-- <input type="button" class="button" :value="allows_duplicates ? 'allows duplicates' : 'disallows duplicates'" @click="allows_duplicates = !allows_duplicates" /> -->
				<ToggleButton
					class="toggle-button"
					truthy="allow duplicates"
					falsy="disallow duplicates"
					:default="allows_duplicates"
					@toggle="allows_duplicates = !allows_duplicates" />
				<ToggleButton
					class="toggle-button"
					truthy="default hide traits"
					falsy="default show traits"
					:default="default_settings?.hidden ?? false"
					@toggle="mutate_default_settings({'hidden': !default_settings?.hidden}); retrieve_default_settings()" />
				<ToggleButton
					class="toggle-button"
					truthy="default restrict location"
					falsy="default allow locations"
					:default="traitset?.locationRestricted ?? false"
					@toggle="mutate_traitset({'locationRestricted': !traitset.locationRestricted}); retrieve_traitset()" />
				<h4>default limit</h4>
				<div id="traitset-limit">
					<input type="button" class="button-mnml" value="⊖" @click="traitset_limit--" />
					{{ traitset_limit }}
					<input type="button" class="button-mnml" value="⊕" @click="traitset_limit++" />
				</div>
				<h4>available to entity types</h4>
				<div id="entity-types">
					<div class="entity-type" :class="entity_types.includes('character') ? 'active': 'inactive'">
						<input type="checkbox" id="character" value="character" v-model="entity_types" />
						<label for="character">Characters</label>
					</div>
					<div class="entity-type" :class="entity_types.includes('faction') ? 'active': 'inactive'">
						<input type="checkbox" id="faction" value="faction" v-model="entity_types" />
						<label for="faction">Factions</label>
					</div>
					<div class="entity-type" :class="entity_types.includes('npc') ? 'active': 'inactive'">
						<input type="checkbox" id="npc" value="npc" v-model="entity_types" />
						<label for="npc">NPCs</label>
					</div>
					<div class="entity-type" :class="entity_types.includes('asset') ? 'active': 'inactive'">
						<input type="checkbox" id="asset" value="asset" v-model="entity_types" />
						<label for="asset">Assets</label>
					</div>
					<div class="entity-type" :class="entity_types.includes('location') ? 'active': 'inactive'">
						<input type="checkbox" id="locations" value="location" v-model="entity_types" />
						<label for="location">Locations</label>
					</div>
					<div class="entity-type" :class="entity_types.includes('gm') ? 'active': 'inactive'">
						<input type="checkbox" id="gm" value="gm" v-model="entity_types" />
						<label for="gm">GM</label>
					</div>
					<div class="entity-type" :class="entity_types.includes('subtrait') ? 'active': 'inactive'">
						<input type="checkbox" id="subtrait" value="subtrait" v-model="entity_types" />
						<label for="subtrait">Subtraits</label>
					</div>
				</div>
				<div id="sfxs">
					<h2>traitset sfx's</h2>
					<div class="sfx-list">
						<SFX v-for="sfx in new_sfxs" :key="sfx.id"
							:sfx_id="sfx.id"
							editing
							@remove="remove_sfx(sfx)" />
					</div>
					<h3 :class="{ 'title-active': adding_sfx }" @click="adding_sfx = !adding_sfx">add sfx</h3>
					<div class="sfx-list" v-if="adding_sfx">
						<SFX v-for="sfx in sfx_list" :key="sfx.id"
							:sfx_id="sfx.id"
							adding
							@add="add_sfx(sfx)" />
					</div>
				</div>
				<div class="locations">locations enabled/disabled</div>
				<LocationSelector location_key="2"
					:locations_enabled="new_locations_enabled"
					:locations_disabled="new_locations_disabled"
					@update="update_locations" />
				<input type="button"
					id="save-traitset-button" class="button" :class="{ 'traitset-changed': traitset_changed }"
					value="save"
					@click="update_traitset" />
			</div>
			<h2 @click="toggle_defaults">trait defaults</h2>
			<div class="default-settings" v-if="show_defaults">
				<input type="button" class="refresh button" value="⟳"
					@click="retrieve_default_settings" />
				<input type="button" class="button" :value="new_traitset_rating_type"
					@click="new_traitset_rating_type = increase_rating_type(new_traitset_rating_type)" />
				<input type="button" class="button"
					:value="player_can_change_rating ? 'players can change rating': 'players can\'t change rating'"
					@click="player_can_change_rating = !player_can_change_rating" />
				<div class="rating">
					default trait rating
					<div class="default-rating" v-if="!show_default_rating">
						<Die v-for="d in new_traitset_rating" :key="d.id"
							:die="d" @click="pick_default_rating = true" />
						<!-- <div class="add-die">+</div> -->
					</div>
					<DiePicker class="pick-rating"
						:dice="new_traitset_rating"
						preview
						v-if="show_default_rating"
						@change-die="change_taitset_default_rating" />
				</div>
				<div class="sfxs">
					<div>
						default trait SFX's
						<input type="button" class="button" :value="show_trait_default_sfx ? 'hide' : 'show'" @click="show_trait_default_sfx = !show_trait_default_sfx" />
					</div>
					<div>
						current:
						<input type="button" class="button"
							v-for="sfx in sfx_list.filter((sfx) => new_trait_default_sfxs.includes(sfx.id))" :key="sfx.id" :value="sfx.name"
							@click="toggle_sfx(sfx.id)" />
					</div>
					<div>
						optional:
						<div v-if="show_trait_default_sfx">
							<input type="button" class="button"
								v-for="sfx in sfx_list.filter((sfx) => !new_trait_default_sfxs.includes(sfx.id))" :key="sfx.id" :value="sfx.name"
								@click="toggle_sfx(sfx.id)" />
						</div>
					</div>
				</div>
				<input type="button" class="button" value="apply" @click="change_default_traitset_settings" />
				<input type="button" class="button" value="cancel" />
			</div>
		</div>
		<div class="traits">
			<h2>traits</h2>
			<!-- <Trait v-for="trait in traitset.traits" :trait_id="trait.id" :key="trait.id" viewing /> -->
			<TraitEdit v-for="trait in traitset.traits"
				:trait_id="trait.id"
				:trait_name="trait.name"
				:key="trait.id" default
				v-if="player.is_gm" @refetch_traits="retrieve_traitset" />
			<div id="trait-creation" v-if="player.is_gm">
				<h3>create new trait</h3>
				<input type="text" v-model="new_trait_name" placeholder="new trait name" />
				<div class="trait-details" v-if="new_trait_name">
					<!-- <div>
						default rating
						<Die class="default-rating-die" :die="{rating: d}"
							v-if="new_trait_rating.length > 0"
							v-for="d in new_trait_rating" @click="new_trait_rating = []" />
						<DiePicker @pick-die="(d: string) => new_trait_rating = [d]" v-else />
					</div> -->
					<!-- <div>required traits</div>
					<div>available sfxs</div>
					<div>locations enabled/disabled</div> -->
					<input type="button" class="button"
						:value="'add (' + new_trait_name + ') to ' + traitset.name"
						@click="create_trait(new_trait_name); retrieve_traitset()" />
				</div>
			</div>
		</div>
		<div class="bottom-scroll-space scroll-space"></div>
	</div>
</template>

<style scoped>
#traitset-view {
	padding-top: 4em;
	.refresh {
		float: right;
	}
	#traitset-settings {
		#save-traitset-button.traitset-changed {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
		}
		#explainer {
			width: 100%;
			min-height: 100px;
		}
		.toggle-button {
			padding: 1em 0;
			max-width: 500px;
			margin: 0 auto;
		}
		#traitset-limit {
			font-size: 2em;
			.button-mnml {
				font-size: 1.2em;
			}
		}
		#entity-types {
			text-align: left;
			display: flex;
			flex-direction: column;
			align-items: center;
			font-size: 1.2em;
			.entity-type {
				background-color: var(--color-background-mute);
				width: 40%;
				min-width: 300px;
				padding: 0 1em;
				label {
					display: inline-block;
					padding: .2em 1em;
				}
				&.inactive {
					color: var(--color-disabled);
				}
			}
		}
		#sfxs {
			.sfx-list {
				width: 100%;
			}
		}
	}
	.trait-details {
		padding-left: 1em;
		.location {
			font-style: italic;
			cursor: pointer;
			.enabled {
				color: var(--color-highlight);
			}
			.disabled {
				color: var(--color-hitch);
			}
			&:hover {
				color: var(--color-highlight);
			}
		}
	}
	.default-rating-die {
		cursor: pointer;
	}
	.bottom-scroll-space {
		height: 100px;
	}
}
</style>
