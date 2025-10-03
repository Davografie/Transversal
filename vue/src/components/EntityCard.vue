<script setup lang="ts">
	import { ref, computed, watch } from 'vue'

	// import Die from './Die.vue'
	import { useEntity } from '@/composables/Entity'
	// import { useDicepoolStore } from '@/stores/DicepoolStore'
	import { usePlayer } from '@/stores/Player'

	import type { Character as CharacterType } from '@/interfaces/Types'

	const player = usePlayer()
	// const dicepool = useDicepoolStore()

	const props = defineProps({
		entity_id:			{	type: String,	required: true	},
		show_unavailable:	{	type: Boolean,	default: false	},
		override_click:		{	type: Boolean,	default: false	},
		show_archetypes:	{	type: Boolean,	default: false	},
		show_icon:			{	type: Boolean,	default: false	},
		show_name:			{	type: Boolean,	default: true	},
		is_relationship:	{	type: Boolean,	default: false	},
		is_follower:		{	type: Boolean,	default: false	},
		is_active:			{	type: Boolean,	default: undefined	},
		options_direction:	{	type: String,	default: 'right'	},
	})

	const emit = defineEmits([
		'refresh_favorites',	// done after long-pressing the card changing its favorite status
		'hide_location',		// after navigating to the entity of the card
		'click_entity',			// after clicking the card
	])


	// prepare the entity variable for the card
	const {
		entity,
		retrieve_small_entity,
		retrieve_followers,
		set_entity_id,
		create_relation,
		entity_type_icon,
	} = useEntity(undefined, props.entity_id)

	retrieve_small_entity()
	retrieve_followers()	// this doesn't get triggered as often as it should yet
							// it should also update in locations when the presence is polled

	watch(() => props.entity_id, (newEntityId) => {
		if(entity.value?.id != newEntityId) {
			set_entity_id(props.entity_id)
			retrieve_small_entity()
		}
	})

	const visible = computed(() => {
		if(entity.value.key == '1') {
			// hide GM
			return false
		}
		else if(
			entity.value.entityType == 'character'
			&& player.is_player
			&& player.the_entity?.id != entity.value.id
			&& props.show_unavailable
		) {
			return (entity.value as CharacterType).available ?? true
		}
		else if(entity.value.isArchetype && player.is_player && !props.show_archetypes) {
			return false
		}
		else {
			return true
		}
	})


	// the entity displayed in the card is the same as the entity that's currently being played with
	const current_character = computed(() => {
		return (player.is_gm && player.perspective.id == entity.value.id) ||
			(!player.is_gm && player.player_character_key == entity.value.key)
	})


	// add the entity of this card as a relation to the codex of the entity that's currently being played with
	function click_tag() {
		if(player.is_gm && player.perspective) {
			create_relation(player.perspective.id)
			player.retrieve_perspective_relations()
		}
		else if(!player.is_gm && player.player_character) {
			create_relation(player.player_character.id)
			player.retrieve_relations()
		}
		retrieve_small_entity()
		editing_card.value = false
	}


	// set the entity of this card as the entity that's played with
	function click_icon() {
		if(player.is_gm) {
			player.perspective.id = entity.value.id
			editing_card.value = false
		}
	}


	// check to see if the entity of this card can be added as a relation
	const relation_possible = computed(() => {
		if(player.is_gm && player.perspective.id) {
			return !player.perspective.relations?.map(r => r.toEntity.id).includes(entity.value.id) &&
				player.perspective.id != entity.value.id
		}
		else if(!player.is_gm && player.player_character) {
			return !player.player_character.relations?.map(r => r.toEntity.id).includes(entity.value.id) &&
				player.player_character.id != entity.value.id
		}
	})


	// when clicking the entity card, navigate to the entity page
	function click_card() {
		if(
			!held.value
		) {
			if(props.override_click) {
				emit('click_entity')
			}
			else {
				editing_card.value = !editing_card.value
			}
		}
	}


	// variable that tracks long-press to favorite an entity
	const held = ref(false)
	const editing_card = ref(false)

	function longpress_card() {
		if(!props.is_follower && props.options_direction != 'none') {
			held.value = true
			editing_card.value = !editing_card.value
			setTimeout(() => held.value = false, 500)
		}
	}


	// when the player wants to follow the entity instead of transversing themselves
	const followable = computed(() => {
		return player.the_entity?.following?.id != entity.value.id	// already following
			&& player.the_entity?.id != entity.value.id				// can't follow yourself
			&& player.the_entity?.entityType != 'location'			// locations can't follow
			&& !(player.is_player && props.is_relationship)			// GM can follow from distance, players can't
			&& !entity.value.isArchetype							// archetypes aren't actually part of the environment (yet)
			// && (
			// 	// anyone can enter an asset
			// 	entity.value.entityType == 'asset'
			// 	// following a faction is group travel
			// 	|| entity.value.entityType == 'faction'
			// 	// npc's can follow npc's
			// 	|| (player.perspective.entityType == 'npc' && entity.value.entityType == 'npc')
			// 	// GM's can follow characters
			// 	|| (player.is_gm && player.perspective.id == 'Entities/1' && entity.value.entityType == 'character')
			// )
	})

	function click_follow() {
		player.is_player ? player.set_location(entity.value) : player.set_perspective_location(entity.value)
		editing_card.value = false
	}

	function click_unfollow() {
		if(player.the_entity?.location) {
			player.is_player ? player.set_location(player.the_entity.location) : player.set_perspective_location(player.the_entity.location)
		}
		editing_card.value = false
	}
	

	// styling variables
	const image_link_small = computed (() => {
		if(entity.value.archetype) {
			return '/assets/uploads/' + entity.value.archetype.id.split('/').pop() + '/small' + entity.value.archetype.image?.ext
		}
		else if (entity.value.image) {
			return '/assets/uploads/' + entity.value.image.path + '/small' + entity.value.image?.ext
		}
		else {
			return '/assets/uploads/' + entity.value.entityType + '/small.png'
		}
	})

	const backgroundStyle = computed(() => {
		return {
			backgroundImage: `url(${image_link_small.value})`,
			backgroundSize: 'cover',
			backgroundPosition: 'center 10%',
		};
	})
</script>

<template>
	<div :to="'/entity/' + entity?.key"
			class="entity-card"
			:class="[
				entity.image ? '' : 'no-image',
				{ 'current': current_character || player.the_entity?.following?.id == entity.id },
				{ 'favorite': player.is_gm && entity.favorite },
				{ 'archetype': entity.isArchetype },
				{ 'editing': editing_card },
				{ 'active': props.is_active ?? entity.active },
				entity.entityType,
				editing_card || (
					(props.is_active ?? entity.active)
					|| entity.entityType == 'faction'
					|| props.is_relationship
				) ? 'clear' : 'faded'
			]"
			@click="click_card"
			v-touch:hold="longpress_card"
			@click.right="longpress_card"
			@contextmenu="(e) => e.preventDefault()"
			v-if="visible">
		<div class="card-wrapper" :style="backgroundStyle">
		</div>
		<p class="archetype-label" v-if="entity.isArchetype">*</p>
		<p class="name" v-if="props.show_name">{{ entity?.name }}</p>
		<transition name="options-transition">
			<div class="options" :class="props.options_direction" v-if="editing_card">
				<!-- <div class="name">{{ entity?.name }}</div> -->
				<div class="button-mnml codex-button"
						:class="{ 'small-button': !player.small_buttons }"
						@click.stop="click_tag"
						v-if="relation_possible">
					<span class="icon">🏷</span>
					<span class="label">{{ player.small_buttons ? '' : '\nadd to contacts'}}</span>
				</div>
				<div class="button-mnml entity-type-icon"
						@click.stop="click_icon"
						v-if="props.show_icon || editing_card">
					<span class="icon">{{ entity_type_icon }}</span>
				</div>
				<div class="button-mnml follow-button"
						:class="{ 'small-button': !player.small_buttons }"
						@click.stop="click_follow"
						v-if="followable">
					<span class="icon">⬆</span>
					<span class="label">{{ player.small_buttons ? '' : entity.entityType != 'location' ? '\nfollow' : '\ntransverse'}}</span>
				</div>
				<div class="button-mnml unfollow-button"
						@click.stop="click_unfollow"
						v-if="player.the_entity?.following && player.the_entity?.following.id == entity.id">
					<span class="icon">⍏</span>
					<span class="label">{{ player.small_buttons ? '' : '\nunfollow'}}</span>
				</div>
			</div>
		</transition>
	</div>
</template>

<style>
	/* not scoped because it's used by other components:
	- CharacterOverview
	- LocationView */
	/* .entity-card.faction {
		height: 50px;
		width: 200px;
		.card-wrapper {
			height: inherit;
			width: inherit;
		}
	} */
	.entity-card {
		text-align: center;
		position: relative;
		padding: 0;
		cursor: pointer;
		width: 100px;
		text-shadow: var(--text-shadow);
		.options {
			interpolate-size: allow-keywords;
			position: absolute;
			display: flex;
			gap: 1em;
			align-items: center;
			/* background-color: var(--color-background-mute); */
			backdrop-filter: blur(3px);
			box-shadow: inset 0 0 100px var(--color-background-mute);
			width: auto;
			max-width: 60vw;
			overflow: hidden;
			&.right {
				left: 50%;
				top: 0;
				height: 100%;
				padding-left: 50px;
				padding-right: 1em;
				border-radius: 0 40px 40px 0;
			}
			&.left {
				right: 50%;
				top: 0;
				height: 100%;
				padding-right: 50px;
				padding-left: 1em;
				border-radius: 40px 0 0 40px;
			}
			&.bottom {
				top: 100%;
				left: 0;
				width: 100%;
				flex-direction: column;
			}
			&.top {
				bottom: 100%;
				left: 0;
				width: 100%;
				flex-direction: column;
			}
			&.inside {
				top: 50%;
				left: 50%;
				transform: translate(-50%, -50%);
				/* position: absolute; */
				z-index: 2;
				width: inherit;
				height: inherit;
				border-radius: inherit;
			}
			> .button-mnml {
				.icon{
					font-size: 1.6em;
				}
			}
			.name {
				padding: .4em 0;
				max-height: 100%;
				/* overflow: hidden; */
				/* width: fit-content; */
				font-size: 1.2em;
				/* text-wrap: nowrap; */
			}
			.codex-button {
				text-align: left;
				padding: 0 .4em;
			}
		}
		.options-transition-enter-active,
		.options-transition-leave-active {
			transition: all 1s ease;
		}
		.options-transition-enter-from,
		.options-transition-leave-to {
			width: 0;
			padding-left: 0 !important;
		}
		.options-transition-enter-to,
		.options-transition-leave-from {
			width: auto;
			padding-left: 1em;
		}
		.card-wrapper {
			height: inherit;
			width: inherit;
			display: flex;
			flex-direction: column;
			border-radius: inherit;
			justify-content: end;
			color: var(--color-text);
			padding: 0.5rem;
			position: relative;
			z-index: 1;
			/* background-image: linear-gradient(to top, var(--color-background) 0, var(--color-background-mute) 15%, transparent 30%); */
			p {
				vertical-align: middle;
			}
			input {
				display: block;
			}
			.followers {
				position: absolute;
				display: flex;
				gap: .2em;
				left: 50%;
				transform: translateX(-50%);
				bottom: -1.6em;
				.follower {
					height: 32px;
					width: 32px;
					.card-wrapper {
						border-width: 2px;
					}
					.name {
						display: none;
					}
				}
			}
			.dice {
				position: absolute;
				height: 140px;
				overflow: hidden;
				top: -20px;
				width: 120px;
				left: -10px;
				display: flex;
				flex-wrap: wrap;
				justify-content: space-between;
				align-content: space-between;
				gap: 2px;
				.die {
					margin: 2px;
				}
			}
			.score {
				font-size: .8em;
				position: absolute;
				top: 0px;
				right: 2px;
				color: var(--color-border);
			}
			.availability {
				font-size: .8em;
				position: absolute;
				bottom: 2px;
				right: 4px;
				color: var(--color-border);
			}
			.live .availability {
				color: var(--color-highlight);
			}
			.subtitle {
				font-size: .8em;
			}
			.vision {
				font-style: italic;
				font-size: .8em;
			}
		}
		&.no-image {
			.card-wrapper {
				border: 1px solid var(--color-border);
			}
			background-color: var(--color-background-mute);
		}
		&.faded {
			color: var(--color-text);
			.card-wrapper {
				background-color: var(--color-background-mute);
			}
		}
		&.live {
			color: var(--color-highlight);
		}
		&.favorite {
			.name {
				color: var(--color-highlight);
			}
		}
		&.archetype {
			.archetype-label {
				position: absolute;
				z-index: 1;
				font-size: 2em;
				top: .4em;
				right: 0;
				line-height: 0;
			}
			.card-wrapper {
				background-color: var(--color-background-mute);
			}
		}
	}
	.dark {
		.entity-card {
			border-radius: 200px;
			box-shadow: 0 0 20px var(--color-background);
			border: 1px solid var(--color-background-mute);
			height: 100px;
			.name {
				position: absolute;
				left: 0;
				right: 0;
				bottom: 0;
				transform: translateY(20%);
				text-align: center;
				font-weight: bold;
				-webkit-font-smoothing: antialiased;
				z-index: 5;
			}
			.button {
				border: 1px solid var(--color-border);
				border-radius: 20px;
				padding: 0 .6em;
				background-color: var(--color-background-mute);
			}
			.entity-type-icon {
				text-shadow: none;
			}
			&.faded {
				opacity: .6;
			}
		}
		.entity-card.current,
		.entity-card.active {
			box-shadow: 0 0 20px var(--color-highlight);
			border: none;
			.card-wrapper {
				border: 3px solid var(--color-highlight);
			}
		}
		.entity-card:hover {
			box-shadow: 0 0 10px var(--color-text);
		}
	}
	.light {
		.entity-card {
			box-sizing: content-box;
			border: 1px solid var(--color-border);
			.card-wrapper {
				height: 100px;
			}
			.name {
				background-color: var(--color-background-soft);
			}
			.codex-button, .entity-type-icon, .follow-button {
				text-shadow: 0 0 5px var(--color-background), 0 0 5px var(--color-background);
				border-radius: 20px;
				background-color: var(--color-background-mute);
				border: 1px solid var(--color-border);
				span {
					display: block;
				}
			}
			.codex-button.small-button {
				width: 80%;
				text-align: center;
				transform: translateX(40px) translateY(-20px);
			}
			.follow-button.small-button {
				width: 80%;
				transform: translateX(-40px) translateY(20px);
			}
			&.current {
				border: 3px solid var(--color-highlight);
				box-shadow: 0 0 20px var(--color-highlight);
			}
			&.faded {
				.card-wrapper {
					border: 2px dashed var(--color-border-hover);
				}
			}
			&:hover {
				.card-wrapper {
					border: 3px solid var(--color-border-hover);
				}
			}
		}
	}
</style>
