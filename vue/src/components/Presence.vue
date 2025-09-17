<script setup lang="ts">
	import { computed, inject } from 'vue'
	import { useLocation } from '@/composables/Location'
	import { usePlayer } from '@/stores/Player'

	import EntityCard from '@/components/EntityCard.vue'

	const props = defineProps<{
		location_key: string,
		search?: string,
		level: number
	}>()

	const emit = defineEmits([
		'click_entity'
	])

	const player = usePlayer()
	const {
		location,
		retrieve_small_location,
		retrieve_presence,
		retrieve_zones
	} = useLocation(undefined, props.location_key)

	retrieve_small_location()
	retrieve_presence()
	if(props.level < 0) retrieve_zones()

	const filtered_presence = computed(() => {
		return location.value.entities?.filter(
			e => (e.entityType != 'gm' && e.entityType != 'faction' && !e.isArchetype)
				&& (
					player.is_gm									// always show to GM
					|| (e.entityType == 'character' && e.active)	// show active characters
					|| (
						e.entityType == 'npc'						// show known NPCs
						&& (
							e.knownTo?.map(kt => kt.id).includes(player.player_character?.id ?? '')
						)
					)
				)
				&& (
					!props.search || e.name.toLowerCase().includes(props.search?.toLowerCase() ?? '')
				)
			)
	})

	const header_size = computed(() => {
		return 1.2 - (props.level * -0.1)
	})
	
	const MEDIA_FOLDER = inject('MEDIA_FOLDER')

	const backgroundImage = computed(() => {
		if(location.value.image) {
			return `background-image: url('${MEDIA_FOLDER + location.value.image.path + 'large' + location.value.image.ext}')`
		}
		else {
			return ''
		}
	})
</script>

<template>
	<div class="parent-location-inheritance"
			:class="[{ 'super': props.level > 0, 'transversable': props.level == 0, 'zone': props.level < 0 }]"
			:style="backgroundImage"
			v-if="(filtered_presence && filtered_presence.length > 0) || (location.zones && location.zones.length > 0)">
		<div class="parent-location-name">
			{{ location.name }}
		</div>
		<div class="entity-cards">
			<template v-for="entity in filtered_presence" :key="entity.key">
				<EntityCard
					:entity_id="entity.id"
					is_active
					override_click
					@click_entity="$emit('click_entity', entity.id)" />
			</template>
		</div>
		<div class="zones">
			<Presence
				class="neighboring-location"
				v-for="neigbor_location in location.zones ?? []"
				:key="neigbor_location.key"
				:location_key="neigbor_location.key"
				:search="props.search"
				:level="props.level - 1"
				@click_entity="(ett_id) => $emit('click_entity', ett_id)"
				v-if="props.level < 0" />
		</div>
	</div>
</template>

<style scoped>
.parent-location-inheritance {
	flex-grow: 1;
	border: 1px solid var(--color-border);
	background-size: cover;
	background-position: center;
	.parent-location-name {
		text-align: left;
		padding-left: .4em;
		font-size: v-bind("header_size + 'em'");
	}
	.entity-cards {
		display: flex;
		justify-content: center;
		flex-wrap: wrap;
		align-items: center;
		/* padding: .4em .2em 1em .2em; */
		padding: 4em;
		gap: 1em;
	}
	.zones {
		display: flex;
		flex-wrap: wrap;
		padding: 1em;
		gap: 1em;
	}
}
</style>

<style>
.dark {
	.entities {
		.drawer {
			.parent-location-inheritance {
				box-shadow: inset 0 0 100px var(--color-background);
				&.super {
					.parent-location-name {
						background-image: linear-gradient(to right, var(--color-positive-die-12) 0%, rgba(0, 0, 0, 0) 80%);
						color: var(--color-positive-die-12-text);
						text-shadow: var(--color-positive-die-12-text-outline) 0px 0px 5px;
					}
				}
				&.transversable {
					.parent-location-name {
						background-image: linear-gradient(to right, var(--color-highlight) -50%, rgba(0, 0, 0, 0) 80%);
						color: var(--color-highlight-text);
						text-shadow: var(--color-highlight) 0px 0px 5px;
					}
				}
				&.zone {
					.parent-location-name {
						background-image: linear-gradient(to right, var(--color-background) 0%, rgba(0, 0, 0, 0) 80%);
						color: var(--color-text);
					}
				}
			}
		}
	}
}
</style>
