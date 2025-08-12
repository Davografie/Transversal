<script setup lang="ts">
	import { watch, ref, onMounted } from 'vue'
	import { useRouter } from 'vue-router'
	import { templateRef, useScroll, useElementBounding } from '@vueuse/core'

	import { useLocation } from '@/composables/Location'

	import Location from '@/components/Location.vue'

	import { usePlayer } from '@/stores/Player'

	import type { Location as LocationType } from '@/interfaces/Types'

	const player = usePlayer()
	const router = useRouter()
	
	const props = defineProps<{
		location_key: string,
		active_entity_id?: string
	}>()

	const emit = defineEmits([
		'transverse',
		'show_entity',
	])

	const {
		location,
		retrieve_parents,
		retrieve_transversables,
		set_location_key
	} = useLocation(undefined, props.location_key)

	const {
		location: parent_location,
		retrieve_small_location: retrieve_parent_location,
		set_location_key: set_parent_location_key
	} = useLocation(undefined, location.value.parent?.key)

	const panel = templateRef<HTMLElement>('panel')
	const { y } = useScroll(panel)
	const { left, width } = useElementBounding(panel)

	const image_link = ref('')

	watch(() => props.location_key, (newLocationKey) => {
		console.log("CurrentLocationView newLocationKey: " + newLocationKey)
		set_location_key(newLocationKey)
		retrieve_parents()
		retrieve_transversables()
		panel.value?.scrollTo(0, 0)
	})

	watch(() => props.active_entity_id, () => {
		panel.value?.scrollTo(0, 0)
	})

	watch(() => location.value.parent, (newParent) => {
		if(newParent) {
			set_parent_location_key(newParent.key)
			// retrieve_parent_location()
		}
	})

	watch(parent_location, (newLocation) => {
		if(newLocation.image) {
			const version = player.data_saving ? 'small' : 'original'
			image_link.value = '/assets/uploads/' + newLocation.image.path + '/' + version + newLocation.image.ext
		}
		else {
			image_link.value = ''
		}
	})

	function transverse(loc: LocationType) {
		panel.value?.scrollTo(0, 0)
		if(player.is_player && player.player_character && loc) {
			player.set_location(loc)
		}
		else if(player.is_gm && player.perspective && loc) {
			player.set_perspective_location(loc)
		}
		console.log("transversing to: " + loc.name)
		router.push({ path: '/location/' + loc.key })
		emit('transverse')
	}

	function click_parent() {
		if(player.is_gm && location.value.parent) {
			// router.push('/Location/' + location.value.parent.key)
			// emit('hide-current-location')
			transverse(location.value.parent)
		}
		else if(player.is_player && player.player_character && location.value.parent) {
			transverse(location.value.parent)
		}
	}

	onMounted(() => {
		console.log("CurrentLocationView mounted")
		retrieve_parents()
		retrieve_transversables()
	})
</script>

<template>
	<div class="container"
			:class="[player.orientation, parent_location.image ? 'image' : 'no-image']"
			:style="{ backgroundImage: `url('${image_link}')`}">
		<div id="parent-location-wrapper" ref="panel">
			<div id="current-location-wrapper" v-if="player.the_entity?.location">
				<div v-if="location.parent" class="parent-location-header">
					<div class="parent-location">
						<h3 class="parent-location-name" @click="click_parent">
							{{ location.parent.name }}
						</h3>
					</div>
				</div>
				<Location id="current-location"
					:loc="props.location_key"
					:key="props.location_key"
					:level="0"
					:show_levels="1"
					:scroll_y="y"
					:active_entity_id="props.active_entity_id"
					:parent_left="left"
					:parent_width="width"
					zone
					@transverse="transverse"
					@show_entity="(entity_key) => emit('show_entity', entity_key)" />
				<div id="transversables" v-if="location.transversables && location.transversables.length > 0">
					<div class="attribute-header header">
						<span>travel</span>
						<div class="border-bottom"></div>
					</div>
					<div id="transversable-locations" :class="player.is_gm ? 'gm' : 'player'">
						<Location class="transversable-location"
							v-for="transversable_location in location.transversables"
							:key="transversable_location.id"
							:loc="transversable_location.key"
							:level="0"
							:show_levels="0"
							:zone="false"
							:parent_left="left"
							:parent_width="width"
							@transverse="(loc) => transverse(loc)" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
.container {
	position: relative;
	overflow-x: hidden;
	overflow-y: auto;
	height: 100vh;
	#scroll-indicator-wrapper {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 10;
		pointer-events: none;
		.scroll-indicator {
			width: 100%;
			height: 10%;
			/* background-color: var(--color-background-mute); */
			/* &.scroll-indicator-top {
				position: absolute;
				top: 0;
				background-image: linear-gradient(to bottom, var(--color-background-mute), transparent);
			} */
			&.scroll-indicator-bottom {
				position: absolute;
				bottom: 0;
				/* background-image: linear-gradient(to top, var(--color-background), var(--color-background-mute) 10%, transparent); */
			}
			&.hidden {
				opacity: 0;
			}
		}
	}
	&.image {
		text-shadow: var(--text-shadow);
	}
	#parent-location-wrapper {
		position: relative;
		height: 100%;
		/* min-height: 100vh; */
		overflow-x: hidden;
		overflow-y: auto;
		nav {
			position: fixed;
			top: 30vh;
			right: 0;
			z-index: 5;
			cursor: pointer;
			a {
				padding: 2em 1em;
				border-radius: 10px 0 0 10px;
			}
		}
		#current-location-wrapper {
			text-align: center;
			position: relative;
			padding: 1em 3% 6em 3%;
			/* padding-bottom: 4em; */
			display: flex;
			flex-direction: column;
			gap: 1em;
			min-height: 100vh;
			.transverse-parent {
				position: absolute;
				left: 0;
				margin: 0;
				border-radius: 0 20px 20px 0;
				border-left: none;
				top: .4em;
			}
			#location-parents {
				display: flex;
				justify-content: center;
				gap: 1em;
			}
			.parent-location-header {
				display: flex;
				justify-content: center;
			}
			.parent-location {
				cursor: pointer;
				text-align: center;
				display: flex;
				align-items: center;
				.open-location-button {
					padding: 0 1em;
				}
			}
			#transversables {
				display: flex;
				flex-direction: column;
				gap: 1em;
				padding: 4em 0;
				.attribute-header {
					text-align: center;
					.border-bottom {
						height: 1px;
						background-image: linear-gradient(to right, var(--color-border), var(--color-text) 50%, var(--color-border) 90%);
						box-shadow: 0 0 10px var(--color-background);
					}
				}
				#transversable-locations {
					display: flex;
					flex-direction: column;
					gap: 3em;
					.transversable-location {
						flex-grow: 1;
						border: 1px solid var(--color-border);
					}
					&.gm {
						flex-direction: row;
						flex-wrap: wrap;
						.transversable-location {
							background-size: cover auto;
							min-width: 300px;
						}
					}
				}
			}
		}
	}
}
</style>

<style>
	.dark {
		.container {
			background-attachment: fixed;
			#current-location-wrapper {
				background-image: linear-gradient(to bottom, transparent 0, transparent 50%, var(--color-background-mute) 100%);
			}
			#transversables #transversable-locations .transversable-location {
				
			}
		}
	}
	.container.horizontal {
		/* background-position: top left; */
		background-size: v-bind(width + 'px') 100vh;
		background-position: v-bind(left + 'px') top;
		background-repeat: no-repeat;
	}
	.light {
		.container {
			background-attachment: scroll;
			#parent-location-wrapper {
				text-shadow: none;
				.parent-location-header {
					display: flex;
					justify-content: center;
				}
				.parent-location {
					background-color: var(--color-background);
					color: var(--color-text);
					border: 1px solid var(--color-border);
					.open-location-button {
						border-right: 1px solid var(--color-border);
					}
					.parent-location-name {
						padding: .4em .6em;
					}
				}
				#transversables {
					background-color: var(--color-background);
				}
			}
		}
	}
</style>
