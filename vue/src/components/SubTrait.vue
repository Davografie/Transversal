<script setup lang="ts">
	import _ from 'lodash'
	import { marked } from 'marked'

	import { ref, watch, computed } from 'vue'

	import { useTrait } from '@/composables/Trait'
	import { useDie, die_constants } from '@/composables/Die'
	import { useDicepool } from '@/composables/Dicepool'

	import Rating from '@/components/Rating.vue'
	import RatingEdit from '@/components/RatingEdit.vue'

	import { usePlayer } from '@/stores/Player'

	import type { Die as DieType } from '@/interfaces/Types'
	
	const props = defineProps<{
		trait_setting_id: string,
		editing_trait?: boolean,
		entity_id?: string,
		parent_traitset_id?: string
	}>()

	const emit = defineEmits([
		'click_subtrait',
		'next_traitset',
		'remove_subtrait',
	])

	const { is_gm } = usePlayer()

	const {
		trait,
		retrieve_trait,
		mutate_trait_setting,
		unassign_subtrait
	} = useTrait(undefined, undefined, props.trait_setting_id, props.entity_id)

	retrieve_trait()

	const {
		add_die,
		add_complication,
		remove_traitsetting_dice,
		remove_complication_by_traitsetting,
		check_trait,
		check_subtrait,
		change_result_limit,
		traitset_dice
	} = useDicepool()

	const is_in_pool = computed(() => check_trait(props.trait_setting_id) || check_subtrait(props.trait_setting_id))

	const editing = ref(false)
	const editing_rating = ref(false)

	watch(() => props.editing_trait, (newEditing) => {
		if(newEditing == false) {
			editing.value = false
			editing_rating.value = false
		}
	})

	const new_statement = ref<string>(trait.value.statement ?? '')
	const new_notes = ref<string>(trait.value.notes ?? '')
	const new_rating_type = ref<string>(trait.value.ratingType ?? 'empty')
	const new_rating = ref<DieType[]>(_.clone(trait.value.rating) ?? [])

	function switch_to_editing() {
		new_statement.value = trait.value.statement ?? ''
		new_rating_type.value = trait.value.ratingType ?? 'empty'
		new_rating.value = _.clone(trait.value.rating) ?? []
		editing_rating.value = trait.value.ratingType == 'empty' || trait.value.rating?.length == 0
		editing.value = true
	}

	function click_subtrait() {
		if(props.editing_trait) {
			if(!editing.value) {
				switch_to_editing()
			}
		}
		else {
			if(trait.value.rating) {
				if(
					trait.value.ratingType == 'static'
					|| trait.value.ratingType == 'challenge'
				) {
					if(!check_trait(trait.value.traitSettingId ?? '')) {
						for(let die of trait.value.rating) {
							// if the trait is of a subtrait traitset, it should use the parent trait's traitset instead
							if(trait.value.traitset?.entityTypes?.includes('subtrait') && props.parent_traitset_id) {
								die.traitsetId = props.parent_traitset_id
							}
							if(die.number_rating > 0) {
								add_die(_.clone(die))
							}
							else {
								if(is_gm) {
									add_die(_.clone(die))
								}
								else {
									add_complication(_.clone(die))
								}
							}
						}
					}
					else {
						remove_traitsetting_dice(trait.value.traitSettingId ?? '')
						remove_complication_by_traitsetting(trait.value.traitSettingId ?? '')
					}
				}
				else if(
					trait.value.ratingType == 'resource'
					&& new Set(trait.value.rating.map((d) => d.number_rating)).size == 1
				) {
					add_die(_.clone(trait.value.rating[0]))
					new_rating.value = trait.value.rating.slice(1)
					mutate_trait_setting({ 'rating': new_rating.value.map((d) => d.number_rating) })
					retrieve_trait()
				}
			}
			if(traitset_limit_reached.value) {
				emit('next_traitset')
			}
			// emit('click_subtrait')
		}
	}

	const traitset_limit_reached = computed(() => {
		// trait traitset limit
		return [...new Set(traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).map((d) => d.traitsettingId))].length >= (props.traitset_limit ?? 0)
		// dice traitset limit
		// return traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).length < (props.traitset_limit ?? 1)
	})

	function deplete_challenge(die: DieType) {
		if(props.editing_trait && !editing.value) {
			editing.value = true
		}
		else if(props.editing_trait && editing.value) {
			new_rating.value = _.clone(trait.value.rating ?? [])
			new_rating_type.value = trait.value.ratingType ?? 'empty'
			editing_rating.value = true
		}
		else if(trait.value.rating) {
			console.log('depleting challenge: ', die)
			const { die: die_obj, change_type } = useDie(die)
			change_type(die_obj.value.number_rating + 1)
			let new_rating = []
			if(die_obj.value.number_rating != 0) {
				const idx = trait.value.rating.findIndex((d) => d.id == die.id)
				new_rating = [...trait.value.rating]
				new_rating.splice(idx, 1, die_obj.value)
			}
			else {
				new_rating = trait.value.rating.filter((d) => d.id != die.id)
			}
			mutate_trait_setting({ 'rating': new_rating.map((d) => d.number_rating) })
			retrieve_trait()
		}
	}

	function deplete_resource(die: DieType) {
		if(props.editing_trait && !editing.value) {
			editing.value = true
		}
		else if(props.editing_trait && editing.value) {
			new_rating.value = _.clone(trait.value.rating ?? [])
			new_rating_type.value = trait.value.ratingType ?? 'empty'
			editing_rating.value = true
		}
		else if(trait.value.rating) {
			add_die(die)
			change_result_limit(1)
			const new_rating = trait.value.rating.filter((d) => d.id != die.id)
			mutate_trait_setting({ 'rating': new_rating.map((d) => d.number_rating) })
			retrieve_trait()
		}
	}

	function change_rating(rating_type: string, rating: DieType[]) {
		new_rating_type.value = rating_type
		new_rating.value = rating
		editing_rating.value = false
		mutate_trait_setting({
			'ratingType': new_rating_type.value,
			'rating': new_rating.value.map(die => die.number_rating)
		})
	}

	function save_subtrait() {
		mutate_trait_setting({
			'statement': new_statement.value,
			'notes': new_notes.value,
			'ratingType': new_rating_type.value,
			'rating': new_rating.value.map(die => die.number_rating)
		})
		setTimeout(() => {
			retrieve_trait()
		}, 200)
		editing.value = false
	}

	function remove_subtrait() {
		console.log('removing sub-trait: ', props.trait_setting_id)
		// unassign_subtrait(props.trait_setting_id)
		emit('remove_subtrait')
	}
</script>

<template>
	<div class="sub-trait" :class="[
				{ 'active': is_in_pool },
				{ 'editing': editing },
				trait.ratingType != 'empty' ? die_constants.find(dc => Math.max(...(trait.rating?.map(die => Math.abs(die.number_rating)) ?? [0])) == dc.number_rating)?.rating : '',
				trait.ratingType != 'empty' ? Math.max(...(trait.rating?.map(die => die.number_rating) ?? [0])) < 0 ? 'negative' : 'positive' : '',
				trait.ratingType
			]"
			@click.stop="click_subtrait"
			@contextmenu="(e) => e.preventDefault()">
		<div class="neutral" :class="{ 'editing': editing }">
			<span v-if="trait.traitSetting?.fromEntity?.id">🔗</span>
			<div class="buttons" v-if="editing">
				<input type="button" class="button remove-subtrait"
					@click.stop="remove_subtrait"
					value="🗑" />
				<input type="button" class="button save-subtrait"
					@click.stop="save_subtrait"
					value="💾"
					v-if="(trait.statement ?? '') != new_statement
						|| (trait.notes ?? '') != new_notes
						|| trait.ratingType != new_rating_type
						|| JSON.stringify(trait.rating) != JSON.stringify(new_rating)" />
				<input type="button" class="button cancel-edit"
					@click.stop="editing = false"
					value="✖" />
			</div>
			<div class="trait-name-and-statement" :class="[
					{ 'with-statement': (trait.statement ?? '') != ''},
					{ 'header': editing }
				]">
				<div class="trait-name" :class="{ 'editing': editing }">
					{{ trait.name }}
				</div>
				<div class="statement">
					<span v-if="!editing && trait.statement">{{ trait.statement }}</span>
					<span v-if="!editing && trait.notes" v-html="marked(trait.notes)"></span>
					<input type="text" v-if="editing" v-model="new_statement" placeholder="statement" />
					<textarea v-if="editing" v-model="new_notes" placeholder="notes" />
				</div>
			</div>
			<div class="rating">
				<Rating
					:rating="editing ? new_rating : trait.rating"
					:rating-type="editing ? new_rating_type : trait.ratingType"
					:resource="trait.ratingType == 'resource'"
					:challenge="trait.ratingType == 'challenge'"
					@deplete-challenge="deplete_challenge"
					@deplete-resource="deplete_resource"
					@click="editing ? editing_rating = true : undefined"
					v-if="trait.rating && !editing_rating" />
			</div>
		</div>
		<div class="editing-rating" v-if="editing">
			<RatingEdit
				v-if="trait.ratingType && trait.rating"
				:rating_type="new_rating_type"
				:rating="new_rating"
				@change-rating="(rt: string, r: DieType[]) => change_rating(rt, r)"
				@cancel="editing_rating = false" />
		</div>
	</div>
</template>

<style scoped>
	.sub-trait {
		border-radius: 30px;
		overflow: hidden;
		border: 1px solid var(--color-border);
		.neutral {
			display: flex;
			align-items: center;
			text-align: right;
			padding: 0 1em;
			.with-statement {
				.trait-name {
					font-weight: bold;
					/* font-size: .8em; */
				}
				.statement {
					line-height: .8em;
					padding-bottom: .4em;
				}
			}
			.rating {
				margin-left: .4em;
			}
			&.editing {
				width: 100%;
				.trait-name-and-statement {
					flex-grow: 1;
					input[type="text"], textarea {
						width: 100%;
						font-size: 1em;
					}
				}
			}
		}
		&.editing {
			width: 100%;
			font-weight: bold;
			border-radius: 0;
			padding: 1em !important;
			border-left: none !important;
			border-right: none !important;
		}
		&.active .neutral .trait-name {
			font-weight: bold;
		}
		&.editing {
			border-top: 1px solid var(--color-border);
			margin-top: 1em;
			border-bottom: 1px solid var(--color-border);
			margin-bottom: 1em;
			padding: 1em 0;
		}
		&.static {
			border-style: solid;
			border-width: 1px;
		}
		&.resource {
			border-style: dashed;
			border-width: 2px;
		}
		&.d4.negative {
			/* background-image: linear-gradient(45deg, var(--color-negative-die-4) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-negative-die-4);
			border-color: var(--color-negative-die-4);
		}
		&.d6.negative {
			/* background-image: linear-gradient(45deg, var(--color-negative-die-6) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-negative-die-6);
			border-color: var(--color-negative-die-6);
		}
		&.d8.negative {
			/* background-image: linear-gradient(45deg, var(--color-negative-die-8) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-negative-die-8);
			border-color: var(--color-negative-die-8);
		}
		&.d10.negative {
			/* background-image: linear-gradient(45deg, var(--color-negative-die-10) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-negative-die-10);
			border-color: var(--color-negative-die-10);
		}
		&.d12.negative {
			/* background-image: linear-gradient(45deg, var(--color-negative-die-12) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-negative-die-12);
			border-color: var(--color-negative-die-12);
		}
		&.d4.positive {
			/* background-image: linear-gradient(45deg, var(--color-positive-die-4) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-positive-die-4);
			border-color: var(--color-positive-die-4);
		}
		&.d6.positive {
			/* background-image: linear-gradient(45deg, var(--color-positive-die-6) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-positive-die-6);
			border-color: var(--color-positive-die-6);
		}
		&.d8.positive {
			/* background-image: linear-gradient(45deg, var(--color-positive-die-8) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-positive-die-8);
			border-color: var(--color-positive-die-8);
		}
		&.d10.positive {
			/* background-image: linear-gradient(45deg, var(--color-positive-die-10) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-positive-die-10);
			border-color: var(--color-positive-die-10);
		}
		&.d12.positive {
			/* background-image: linear-gradient(45deg, var(--color-positive-die-12) -60%, var(--color-background) 60%); */
			box-shadow: inset 0 0 20px -6px var(--color-positive-die-12);
			border-color: var(--color-positive-die-12);
		}
	}
</style>
