<script setup lang="ts">
	import { ref, watch, onMounted } from 'vue'
	import { templateRef, useScroll } from '@vueuse/core'

	import { usePlayer } from '@/stores/Player'
	import { useEntityList } from '@/composables/EntityList'
	import Relation from '@/components/Relation.vue'
	import EntityCard from '@/components/EntityCard.vue'
	import type { Entity as EntityType, Relation as RelationType } from '@/interfaces/Types'

    const props = defineProps<{
		shown: boolean
    }>()

	const emit = defineEmits([
		'hide_codex',
		'show_entity'
	])

	const player = usePlayer()

	const { entities, retrieve_characters } = useEntityList(undefined, 'character')

	// html elements
	const panel = ref()
	const codexContacts = templateRef<HTMLElement>('codexContacts')
	let { arrivedState } = useScroll(codexContacts)

	const selected_relation = ref<RelationType|null>()
	
	function hide_codex() {
		selected_relation.value = null
		emit('hide_codex')
	}

	onMounted(() => {
		player.retrieve_perspective_relations();
		if(player.is_gm) { retrieve_characters(true) }
		({ arrivedState } = useScroll(codexContacts))
	})
	
	watch(() => props.shown, (newShown) => {
		if (newShown) {
			const { x, y } = useScroll(panel.value)
			y.value = 0
		}
	})

	watch(() => player.the_entity, (newEntity, oldEntity) => {
		if(newEntity && newEntity.id !== oldEntity?.id) {
			player.is_gm ? player.retrieve_perspective_relations() : player.retrieve_relations()
		}
	})

	function click_character(entity: EntityType) {
		if(player.orientation == 'vertical') {
			if(selected_relation.value?.toEntity.id == entity.id) {
				selected_relation.value = null
			}
			else if(player.the_entity?.relations?.find(r => r.toEntity.id == entity.id)) {
				selected_relation.value = player.the_entity?.relations?.find(r => r.toEntity.id == entity.id)
			}
			else {
				selected_relation.value = {
					id: '',
					fromEntity: player.the_entity,
					fromType: player.the_entity?.entityType,
					toEntity: entity,
					toType: 'character'
				}
			}
		}
		else {
			emit('show_entity', entity.id)
		}
	}

	function click_relation(relation: RelationType) {
		if(player.orientation == 'vertical') {
			if(selected_relation.value?.id != relation.id) {
				selected_relation.value = relation
			}
			else {
				selected_relation.value = null
			}
		}
		else {
			emit('show_entity', relation.toEntity.id)
		}
	}
</script>

<template>
	<div class="container" :ref="panel" v-touch:swipe.right="hide_codex">
		<div id="codex-wrapper" :class="player.orientation == 'vertical' ? 'vertical' : 'horizontal'">
			<div id="codex-header" v-if="player.orientation == 'vertical'">
				<h1>contacts</h1>
			</div>
			<div id="codex-contact-list">
				<!-- <div id="scroll-indicator-wrapper">
					<div class="scroll-indicator scroll-indicator-top" :class="{ 'hidden': arrivedState.top }"></div>
					<div class="scroll-indicator scroll-indicator-bottom" :class="{ 'hidden': arrivedState.bottom }"></div>
				</div> -->
				<div id="codex-contacts" ref="codexContacts">
					<div class="top-scroll-space scroll-space" v-if="player.orientation == 'horizontal'"></div>
					<Relation :relation_id="selected_relation.id"
						:from_type="player.the_entity?.entityType"
						:to_entity_id="selected_relation.toEntity?.id"
						:to_type="selected_relation.toEntity?.entityType"
						@hide_codex="hide_codex"
						@hide_relation="selected_relation = null"
						@show_entity="emit('show_entity', $event)"
						v-if="selected_relation && player.orientation == 'vertical'" />
					<div class="mid-scroll-space scroll-space" v-if="player.orientation == 'horizontal'"></div>
					<h2 v-if="player.is_gm && entities.length > 0">
						{{player.orientation == 'vertical' ? 'characters' :  'PCs'}}
					</h2>
					<div class="relations-container" :class="player.orientation == 'vertical' ? 'vertical' : 'horizontal'" v-if="entities.length > 0">
						<template v-for="(entity, index) in entities" :key="entity.id" v-if="player.is_gm">
							<EntityCard
								:entity_id="entity.id"
								override_click
								@click_entity="click_character(entity)" />
						</template>
					</div>
					<h2 v-if="player.is_gm && entities.length > 0 && (player.the_entity?.relations?.length ?? 0) > 0">
						contacts
					</h2>
					<div class="relations-container" :class="player.orientation == 'vertical' ? 'vertical' : 'horizontal'" v-if="(player.the_entity?.relations?.length ?? 0) > 0">
						<template v-for="(relation, index) in player.the_entity?.relations?.filter(r => !entities.map(e => e.id).includes(r.toEntity?.id)) ?? []" :key="relation.id">
							<EntityCard
								:entity_id="relation.toEntity?.id"
								options_direction="none"
								is_relationship
								show_icon
								override_click
								@click_entity="click_relation(relation)" />
						</template>
					</div>
					<!-- <div class="bottom-scroll-space scroll-space"></div> -->
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
	.divider {
		width: 100%;
		height: 1px;
		background-color: var(--color-border);
	}
	.container {
		height: 100vh;
		/* padding-bottom: 4em; */
		position: relative;
		overflow: hidden;
		nav {
			position: fixed;
			top: 30vh;
			left: 0;
			z-index: 5;
			cursor: pointer;
			a {
				padding: 2em 1em;
				border-radius: 0 10px 10px 0;
			}
		}
		#codex-wrapper {
			height: 100vh;
			overflow-y: auto;
			display: flex;
			flex-direction: column;
			#codex-header {
				/* padding-top: 4em; */
				border-bottom: 1px solid var(--color-border);
				overflow: hidden;
			}
			#codex-contact-list {
				position: relative;
				flex-grow: 1;
				#scroll-indicator-wrapper {
					position: absolute;
					top: 0;
					left: 0;
					right: 0;
					bottom: 0;
					z-index: 10;
					pointer-events: none;
					.scroll-indicator {
						width: 100%;
						height: 50px;
						/* background-color: var(--color-background-mute); */
						&.scroll-indicator-top {
							position: absolute;
							top: 0;
							background-image: linear-gradient(to bottom, var(--color-background), var(--color-background-mute) 10%, transparent);
						}
						&.scroll-indicator-bottom {
							position: absolute;
							bottom: 0;
							background-image: linear-gradient(to top, var(--color-background), var(--color-background-mute) 10%, transparent);
						}
						&.hidden {
							opacity: 0;
						}
					}
				}
				h2 {
					background-color: var(--color-background-mute);
					/* color: var(--color-highlight-text); */
					border-bottom: 1px solid var(--color-border);
				}
				#codex-contacts {
					/* height: v-bind(panelHeight - 50 + 'px'); */
					overflow-y: auto;
					overflow-x: hidden;
					position: relative;
					display: flex;
					flex-direction: column;
					.relations-container {
						display: flex;
						flex-direction: column;
						padding: 1em;
						gap: 1em;
						&.vertical {
							flex-direction: row;
							flex-wrap: wrap;
							justify-content: space-around;
						}
					}
					.scroll-space {
						/* background-color: var(--color-background-mute); */
					}
					.top-scroll-space {
						min-height: 1em;
						max-height: 4em;
						flex-grow: 1;
					}
					.mid-scroll-space {
						min-height: .6em;
						flex-grow: 1;
					}
					.bottom-scroll-space {
						min-height: 100px;
						flex-grow: 4;
					}
				}
			}
		}
	}
</style>

<style>
	.dark {
		#codex-wrapper {
			&.vertical {
				background-color: var(--color-background-mute);
			}
			&.horizontal {
				#codex-contacts {
					height: 100%;
					.relations-container, .scroll-space {
						background-image: linear-gradient(to right, var(--color-background-mute) 0%, transparent 20%);
						flex-grow: 1;
					}
				}
			}
			#codex-nav-back a {
				box-shadow: 0 0 10px var(--color-background);
			}
		}
	}
</style>
