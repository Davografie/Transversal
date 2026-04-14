<script setup lang="ts">
	/*
		used on the TraitsetOverview.vue page
	*/
	import { ref, watch, type Ref } from 'vue'
	import { RouterLink } from 'vue-router'
	import useClipboard from 'vue-clipboard3'

	import Die from '@/components/Die.vue'
	import DiePicker from '@/components/DiePicker.vue'
	import LocationSelector from '@/components/LocationSelector.vue'
	import SubtraitSelector from '@/components/SubtraitSelector.vue'
	import ToggleButton from '@/components/UI/ToggleButton.vue'
	import Trait from '@/components/Trait.vue'
	import SFX from '@/components/SFX.vue'
	import { useTrait, rating_types } from '@/composables/Trait'
	import { useSFXList } from '@/composables/SFXList'
	import { useTraitsetList } from '@/composables/TraitsetList'
	import type { Die as DieType, SFX as SFXType, Trait as TraitType, Traitset as TraitsetType } from '@/interfaces/Types'

	const props = defineProps<{
		trait_id: string,
		trait_name: string,
		default?: boolean,
		expanded?: boolean
	}>()

	const emit = defineEmits(['refetch_traits'])

	const {
		trait,
		retrieve_trait,
		retrieve_entities,
		instances,
		retrieve_instances,
		retrieve_statement_examples,
		default_settings,
		retrieve_default_settings,
		create_default_settings,
		retrieve_possible_sfxs,
		mutate_trait,
		mutate_default_settings,
		delete_trait
	} = useTrait(
		undefined,
		props.trait_id,
		undefined,
		undefined
	)

	const { traitsets, retrieve_traitsets } = useTraitsetList(undefined, undefined, undefined)
	
	const { sfx_list, retrieve_sfx_list } = useSFXList()

	const { toClipboard } = useClipboard()
	const copy = async () => {
		try {
			await toClipboard(trait.value.id)
			console.log('Copied to clipboard')
		} catch (e) {
			console.error(e)
		}
	}

	const default_name: Ref<string> = ref("")
	const explanation: Ref<string> = ref("")
	const changing_rating: Ref<boolean> = ref(false)
	const default_rating: Ref<DieType[]> = ref([])
	const default_rating_type = ref(rating_types[0])
	const requirements: Ref<Array<string>> = ref([])
	const new_requirement: Ref<string> = ref("")
	const new_possible_sfx_ids: Ref<Array<string>> = ref([])
	const new_default_sfxs: Ref<Array<string>> = ref([])
	const statement_examples = ref<string[]>([])
	const new_inheritable = ref(false)
	
	const show_details = ref(props.expanded ?? false)
	const refreshing = ref(false)

	if(show_details.value) {
		refresh()
	}

	function toggle_details() {
		if(!show_details.value) {
			refresh()
		}
		// if (trait.value.sfxs) new_default_sfxs.value = trait.value.sfxs.map(x => x.id)
		show_details.value = !show_details.value
	}

	function update_trait() {
		const trait_input = {
			name: default_name.value,
			explanation: explanation.value,
			requiredTraits: requirements.value,
			possibleSubTraits: trait.value.possibleSubTraits?.map(x => x.id),
			inheritable: new_inheritable.value
		}
		mutate_trait(trait_input)
		mutate_default_settings({
			ratingType: default_rating_type.value,
			rating: default_rating.value.map(x => x.number_rating),
			locationsEnabled: default_settings.value?.locationsEnabled,
			locationsDisabled: default_settings.value?.locationsDisabled,
			sfxs: new_default_sfxs.value
		})
		refresh()
		// toggle_details()
	}

	async function refresh() {
		refreshing.value = true
		let trait_completed = false
		let default_completed = false
		await retrieve_trait('network-only')
		await retrieve_instances('network-only')
		// watch(trait, (newTrait) => {
			default_name.value = trait.value.name
			if (trait.value.explanation) explanation.value = trait.value.explanation
			if (trait.value.rating) default_rating.value = trait.value.rating
			if (trait.value.ratingType) default_rating_type.value = trait.value.ratingType
			if (trait.value.requiredTraits) requirements.value = trait.value.requiredTraits.map(x => x.id)
			if (trait.value.traitSetting?.hidden) new_hidden.value = trait.value.traitSetting.hidden
			if (trait.value.inheritable) new_inheritable.value = trait.value.inheritable
			if (trait.value.randomWeight) new_random_weight.value = trait.value.randomWeight
			trait_completed = true
			if(trait_completed && default_completed) refreshing.value = false
		// })
		await retrieve_default_settings('network-only')
		// watch(default_settings, (newDefaults) => {
		// 	console.log("default settings: ", newDefaults)
			if(default_settings.value) {
				default_rating_type.value = default_settings.value.ratingType ?? rating_types[0]
				default_rating.value = default_settings.value.rating ?? []
				new_default_sfxs.value = default_settings.value.sfxs?.map((x: SFXType) => x.id) ?? []
			}
			default_completed = true
			if(trait_completed && default_completed) refreshing.value = false
		// })
	}

	function increase_rating_type(rating_type: string) {
		// cycles through rating types to change trait rating type
		const rating_index: number = rating_types.findIndex(x => x == rating_type)
		changing_rating.value = true
		return rating_types[(rating_index + 1) % rating_types.length]
	}

	/* CHANGE TRAITSET */
	const show_change_traitset = ref(false)
	function toggle_change_traitset() {
		retrieve_traitsets()
		show_change_traitset.value = !show_change_traitset.value
	}
	async function change_traitset(traitset_id: string) {
		await mutate_trait({ traitsetId: traitset_id })
		emit('refetch_traits')
	}


	/* REQUIREMENTS */
	function remove_requirement(trait_id: string) {
		requirements.value = requirements.value.filter(x => x != trait_id)
		update_trait()
	}

	function add_requirement() {
		if(new_requirement.value.length > 0) {
			requirements.value.push(new_requirement.value)
			new_requirement.value = ""
		}
		// retrieve_trait()
		update_trait()
	}

	const show_sfxs = ref(false)
	function toggle_sfx(sfx_id: string) {
		if(new_default_sfxs.value.includes(sfx_id)) {
			const i = new_default_sfxs.value.indexOf(sfx_id)
			new_default_sfxs.value.splice(i, 1)
		}
		else {
			new_default_sfxs.value = [...new_default_sfxs.value, sfx_id]
		}
		mutate_default_settings({ sfxs: new_default_sfxs.value }) // this does work because this is how it's written to the database
	}

	function update_locations(locations_enabled: string[], locations_disabled: string[]) {
		console.log("enabled locations: ", locations_enabled, " disabled: ", locations_disabled)
		const new_default_settings = { locationsEnabled: locations_enabled, locationsDisabled: locations_disabled }
		console.log("new default settings: ", new_default_settings)
		mutate_default_settings(new_default_settings)
	}

	/* SUB-TRAITS */
	import { useTraitList } from '@/composables/TraitList'
	
	const { traits: potential_sub_traits, retrieve_traits } = useTraitList(undefined, 'Traitsets/7702839', undefined, false)
	retrieve_traits()
	const show_subtraits = ref(false)
	const new_subtraits = ref<TraitType[]>([])
	const new_subtraitsets = ref<TraitsetType[]>([])
	const show_linking_subtraits = ref(false)
	function toggle_show_subtraits() {
		retrieve_traitsets()
		show_subtraits.value = !show_subtraits.value
		new_subtraits.value = trait.value.possibleSubTraits ?? []
	}

	async function toggle_subtrait(subtrait: TraitType) {
		if(new_subtraits.value.map(x => x.id).includes(subtrait.id)) {
			const i = new_subtraits.value.findIndex(x => x.id == subtrait.id)
			new_subtraits.value = [...new Set([...new_subtraits.value.slice(0, i), ...new_subtraits.value.slice(i + 1)])]
		}
		else {
			new_subtraits.value = [...new Set([...new_subtraits.value, subtrait])]
		}
		await mutate_trait({
			possibleSubTraits: new_subtraits.value.map(x => x.id)
		})
		// retrieve_trait()
	}

	async function toggle_subtraitset(ts: TraitsetType) {
		console.log("toggling possible subtraitset: ", ts)
		if(trait.value.possibleSubTraitsets?.map(psts => psts.id).includes(ts.id)) {
			new_subtraitsets.value = trait.value.possibleSubTraitsets?.filter(psts => psts.id != ts.id) ?? []
			new_subtraits.value = new_subtraits.value.filter(x => !ts.traits?.map(y => y.id).includes(x.id))
		}
		else {
			new_subtraitsets.value = [...trait.value.possibleSubTraitsets ?? [], ts]
		}
		// if(ts.traits?.every(t => new_subtraits.value.map(x => x.id).includes(t.id))) {
		// 	new_subtraits.value = new_subtraits.value.filter(x => !ts.traits?.map(y => y.id).includes(x.id))
		// }
		// else {
		// 	new_subtraits.value = [
		// 		...new_subtraits.value.filter(x => !ts.traits?.map(y => y.id).includes(x.id)),
		// 		...ts.traits ?? []
		// 	]
		// }
		new_subtraits.value = [...new Set(new_subtraits.value)]

		await mutate_trait({
			possibleSubTraits: new_subtraits.value.map(x => x.id),
			possibleSubTraitsets: new_subtraitsets.value.map(x => x.id)
		})
	}

	/* POSSIBLE SFXS */
	const show_possible_sfxs = ref(false)
	const sfx_list_counter = ref(0) // for updating sfx list
	function toggle_show_sfxs() {
		if(!show_possible_sfxs.value) {
			retrieve_sfx_list()
			retrieve_possible_sfxs('network-only')
		}
		show_possible_sfxs.value = !show_possible_sfxs.value
	}
	async function toggle_possible_sfx(sfx: SFXType) {
		if(new_possible_sfx_ids.value.includes(sfx.id)) {
			const i = new_possible_sfx_ids.value.indexOf(sfx.id)
			new_possible_sfx_ids.value.splice(i, 1)
		}
		else {
			new_possible_sfx_ids.value = [...new_possible_sfx_ids.value, sfx.id]
		}
		await mutate_trait({
			possibleSfxs: new_possible_sfx_ids.value
		})
		await retrieve_possible_sfxs('network-only')
		new_possible_sfx_ids.value = trait.value.possibleSfxs?.map(x => x.id) ?? []
		sfx_list_counter.value++
		// setTimeout(() => {
		// 	retrieve_possible_sfxs()
		// }, 200)
	}
	// watch(() => trait.value.possibleSfxs, () => {
	// 	new_possible_sfx_ids.value = trait.value.possibleSfxs?.map(x => x.id) ?? []
	// })

	const editing_die = ref<DieType|undefined>(undefined)
	function edit_die(die: DieType) {
		editing_die.value = die
		changing_rating.value = true
	}

	function apply() {
		update_trait()
		retrieve_trait()
	}

	const show_instances = ref(false)
	function toggle_instances() {
		if(!instances.value || instances.value.length == 0) retrieve_instances()
		show_instances.value = !show_instances.value
	}

	const show_entities = ref(false)
	function toggle_entities() {
		if(!trait.value.entities) retrieve_entities()
		show_entities.value = !show_entities.value
	}

	const show_statement_examples = ref(false)
	function toggle_statement_examples() {
		if(!statement_examples.value || statement_examples.value.length == 0) {
			retrieve_statement_examples().then(x => statement_examples.value = x)
		}
		show_statement_examples.value = !show_statement_examples.value
	}

	const show_default = ref(false)
	async function toggle_default() {
		await retrieve_default_settings('network-only')
		if(!default_settings.value || default_settings.value.traitSettingType != 'Traits') await create_default_settings()
		show_default.value = !show_default.value
	}

	const show_locations = ref(false)
	const show_required = ref(false)

	function change_default_rating(d: DieType[]) {
		default_rating.value = d;
		changing_rating.value = false
		update_trait()
	}

	const deleting = ref(false)

	async function confirm_delete_trait() {
		await delete_trait()
		emit('refetch_traits')
	}

	function toggle_inheritable() {
		new_inheritable.value = !new_inheritable.value
		mutate_trait({
			inheritable: new_inheritable.value
		})
	}

	const new_hidden = ref(default_settings.value?.hidden ?? false)
	function toggle_hidden() {
		new_hidden.value = !new_hidden.value
		mutate_default_settings({
			hidden: new_hidden.value
		})
	}

	import ScalingEdit from './ScalingEdit.vue'
	const new_random_weight = ref(trait.value.randomWeight ?? 1)
	const show_random_weight = ref(false)
	function toggle_random_weight() {
		show_random_weight.value = !show_random_weight.value
	}
	function set_random_weight(n: number) {
		new_random_weight.value = n
		mutate_trait({ randomWeight: n })
	}
</script>

<template>
	<div class="trait-edit" :class="show_details ? 'expanded' : 'collapsed'">
		<div @click="toggle_details" class="trait-title" :class="show_details ? 'header' : ''">
			{{ props.trait_name }}
		</div>
		<div v-show="show_details" class="trait-details">
			<div class="control-buttons">
				<input type="button" class="copy-id button" title="copy trait id" value="#" @click="copy" />
				<input type="button" class="refresh button" :class="{ 'disabled': refreshing }" title="refresh" value="⟳" @click="refresh" />
				<input type="button" class="delete button" value="🗑" @click="deleting = true" v-if="!deleting" />
				<input type="button" class="delete-y button" value="✅" @click="confirm_delete_trait" v-if="deleting" />
				<input type="button" class="delete-n button" value="❌" @click="deleting = false" v-if="deleting" />
			</div>
			<div id="trait-details">
				<div class="name">
					name
					<input type="text" v-model="default_name" />
				</div>
				<textarea class="explanation" type="text" placeholder="trait explanation" v-model="explanation"></textarea>
				<input type="button" class="button" value="apply" @click="apply" v-if="default_name != trait.name || explanation != trait.explanation" />
				<input type="button" class="button" value="cancel" @click="show_details = false" v-if="default_name != trait.name || explanation != trait.explanation" />
				<ToggleButton truthy="locations inherit this trait"
					falsy="locations do not inherit this trait"
					:default="new_inheritable"
					@toggle="toggle_inheritable" />
				<ToggleButton truthy="this trait is hidden"
					falsy="this trait is visible"
					:default="new_hidden ?? default_settings?.hidden ?? false"
					@toggle="toggle_hidden" />
				<div class="location-restricted">
					<ToggleButton truthy="location restricted"
						falsy="location unrestricted"
						:default="trait.locationRestricted ?? false"
						@toggle="mutate_trait({'locationRestricted': !trait.locationRestricted});" />
					<label for="location-restricted">
						if location restricted, upon assigning trait to entity or relation, the trait will be restricted to the current universe (i.e. the multiverse's direct descendant)
					</label>
				</div>
				
				<h2 @click="toggle_instances">instances</h2>
				<div class="instances" v-if="instances && show_instances">
					<Trait v-for="instance in instances" :key="instance.id"
						:trait_id="trait.id"
						:trait_setting_id="instance.id"
						:entity_id="instance.fromEntity?.id"
						@refetch="retrieve_instances('network-only')"
					/>
				</div>

				<h2 @click="toggle_entities">entities using '{{ default_name }}'</h2>
				<div class="entities" v-if="trait.entities && show_entities">
					<span v-for="(d, i) in trait.entities" class="instance">
						<RouterLink :to="'/entity/' + d.key">
							{{ d.name }}
						</RouterLink>
						{{ i < trait.entities.length - 1 ? '- ' : '' }}
					</span>
				</div>

				<h2 @click="toggle_statement_examples">statement examples</h2>
				<div class="statement-examples" v-if="show_statement_examples && statement_examples">
					<div class="statement-example" v-for="(d, i) in statement_examples">
						{{ d }}
						<div class="statement-example-divider" v-if="i < statement_examples.length - 1"></div>
					</div>
				</div>

				<h2 @click="toggle_random_weight">random weight</h2>
				<div class="random-weight" v-if="show_random_weight">
					<ScalingEdit :scaling="new_random_weight" :min="0" :max="12" @change_scaling="set_random_weight" />
				</div>

				<h2 @click="toggle_change_traitset">change traitset</h2>
				<div class="traitsets" v-if="show_change_traitset">
					<input type="button" class="button" v-for="ts in traitsets" :key="ts.id" :value="ts.name" @click="change_traitset(ts.id)" />
				</div>

				<h2 @click="show_required = !show_required">required traits</h2>
				<div class="required-traits" v-show="show_required">
					<ul>
						<li v-for="d in trait.requiredTraits" class="required-trait">
							<a @click="remove_requirement(d.id)">{{ d.name }}</a>
						</li>
						<li v-for="d in requirements.filter(x => !trait.requiredTraits.map(x => x.id).includes(x))" class="required-trait">
							{{ d }}
						</li>
					</ul>
					<input type="text" placeholder="new requirement" v-model="new_requirement" />
					<input type="button" class="button" value="+" @click="add_requirement" />
				</div>

				<h2 @click="toggle_show_subtraits">possible sub-traits</h2>
				<div class="sub-traits" v-show="show_subtraits">
					<h3>subtrait traitsets</h3>
					<div>
						<SubtraitSelector v-for="ts in traitsets.filter(ts => ts.entityTypes?.includes('subtrait'))" :key="ts.id"
							:traitset_id="ts.id"
							:traitset_name="ts.name"
							:selected_traits="trait.possibleSubTraits?.map(x => x.id)"
							:selected_count="trait.possibleSubTraits?.map(pst => pst.traitset?.id).filter(id => id == ts.id).length"
							@toggle_subtrait="toggle_subtrait"
							@toggle_subtraitset="(traitset: TraitsetType) => toggle_subtraitset(traitset)" />
					</div>
					<h3 @click="show_linking_subtraits = !show_linking_subtraits">allow linked subtraits</h3>
					<div v-if="show_linking_subtraits">
						<SubtraitSelector v-for="ts in traitsets.filter(ts => !ts.entityTypes?.includes('subtrait'))" :key="ts.id"
							:traitset_id="ts.id"
							:traitset_name="ts.name"
							:selected_traits="trait.possibleSubTraits?.map(x => x.id)"
							:selected_count="trait.possibleSubTraits?.map(pst => pst.traitset?.id).filter(id => id == ts.id).length"
							@toggle_subtrait="toggle_subtrait"
							@toggle_subtraitset="(traitset: TraitsetType) => toggle_subtraitset(traitset)" />
					</div>
					<!-- <input type="button" class="button" :value="subtrait.name" v-for="subtrait in potential_sub_traits"
						:class="{ 'active': trait.possibleSubTraits?.map(x => x.id).includes(subtrait.id) }"
						@click="toggle_subtrait(subtrait)" /> -->
				</div>

				<h2 @click="toggle_show_sfxs">sfxs</h2>
				<div class="sfxs" v-if="show_possible_sfxs">
					<SFX class="button"
						v-for="sfx in sfx_list" :key="sfx.id + sfx_list_counter"
						:sfx_id="sfx.id"
						:adding="!trait.possibleSfxs?.map(x => x.id).includes(sfx.id)"
						:editing="trait.possibleSfxs?.map(x => x.id).includes(sfx.id)"
						@add="toggle_possible_sfx(sfx)"
						@remove="toggle_possible_sfx(sfx)"
						:class="{ 'active': trait.possibleSfxs?.map(x => x.id).includes(sfx.id) }" />
				</div>

				<h2 @click="show_locations = !show_locations">locations</h2>
				<div class="locations" v-show="show_locations">
					<LocationSelector location_key="2"
						:locations_enabled="default_settings?.locationsEnabled"
						:locations_disabled="default_settings?.locationsDisabled"
						@update="update_locations" />
				</div>
			</div>

			<h2 @click="toggle_default">default</h2>
			<div id="trait-defaults" v-if="show_default">

				<Trait :trait_setting_id="default_settings?.id" :trait_id="trait.id" />

				<div class="rating">
					<h3>default rating</h3>
					<input type="button" class="button" :value="default_rating_type"
						@click="default_rating_type = increase_rating_type(default_rating_type)" />
					<Die class="default-rating-die"
						v-for="d in default_rating" :die="d"
						v-if="default_settings && default_settings.rating && !changing_rating"
						@click="edit_die(d)" />
					<DiePicker v-else :dice="default_rating"
						@change-die="change_default_rating" show_effects preview />
				</div>
				<div class="sfxs">
					<h3>default SFX's</h3>
					<input type="button" class="button" value="show" @click="show_sfxs = !show_sfxs" />
					<div class="possible_sfxs" v-show="show_sfxs">
						<input type="button" class="button" :class="{ 'active': new_default_sfxs?.includes(sfx.id) }"
							v-for="sfx in sfx_list" :key="sfx.id" :value="sfx.name" @click="toggle_sfx(sfx.id)" />
					</div>
				</div>
				<div class="subtraits">
					<h3>subtraits</h3>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
	.trait-edit.collapsed {
		display: inline-block;
		border: 1px solid var(--color-border);
		border-radius: 25px;
		margin: .2em;
		padding: 0 .8em;
		background-color: var(--color-background);
		vertical-align: middle;
		min-height: 1em;
	}
	.trait-edit.expanded {
		scroll-snap-align: center;
		margin-top: 1em;
		width: 100%;
		max-height: 100%;
		overflow-y: auto;
		.trait-title {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
			font-size: 1.2em;
		}
		.statement-example-divider {
			border-bottom: 1px solid var(--color-border);
		}
		.trait-details {
			padding: 0 1em .4em 1em;
			border-top: 1px solid var(--color-border);
			border-bottom: 1px solid var(--color-border);
			background-color: var(--color-background-mute);
			.explanation {
				min-height: 4em;
				display: block;
				width: 100%;
			}
			.sfxs {
				.active {
					background-color: var(--color-highlight);
					color: var(--color-highlight-text);
				}
			}
			.locations {
				overflow-x: auto;
			}
		}
	}
	.trait-title {
		cursor: pointer;
		text-align: center;
	}
	.control-buttons {
		float: right;
	}
	.default-rating-die {
		cursor: pointer;
	}
	.required-trait a:hover {
		text-decoration: line-through;
		cursor: pointer;
	}
</style>

<style>
	.dark {
		.trait-title {
			text-shadow: none;
		}
	}
</style>
