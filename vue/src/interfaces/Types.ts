export interface Die {
    id?: string
    rating: string
    number_rating: number
    ratingType?: string
    sides?: number
    pool?: boolean
    result?: number
    raises?: number
    isResultDie?: boolean
    isEffectDie?: boolean
    isHitch?: boolean
    isResolved?: boolean
    player?: string
    entityId?: string
    traitsettingId?: string
    subTraitsettingId?: string
    traitId?: string
    sfxId?: string
    traitsetId?: string
    disabled?: boolean
    active?: string
    inactive?: string
}

export interface Dicepool {
    player: string
    dice: Die[]
}

export interface Player {
    uuid: string
    player_name: string
    is_gm: boolean
    phase: string
}

export interface Resolution {
    player: Player
    dice: Die[]
    result?: number
    heroic?: number
    winner?: boolean
}

export interface Session {
    session: string
    scene: string
    beat: string
    dicepoolLimit: number
}

export interface SFX {
    id: string
    name: string
    description: string
}

export interface TraitSetting {
    id?: string
    statement?: string
    notes?: string
    ratingType?: string
    rating?: Die[]
    locationsEnabled?: string[]
    locationsDisabled?: string[]
    sfxs?: SFX[]
    sfxsIds?: string[]
    knownTo?: Character[]
    hidden?: boolean
    resource?: boolean
    fromEntity?: Entity
}

export interface TraitSettingInput {
    statement?: string
    notes?: string
    ratingType?: string
    rating?: number[]
    locationsEnabled?: string[]
    locationsDisabled?: string[]
    sfxs?: string[]
    knownTo?: string[]
    hidden?: boolean
    teachTo?: string
    resource?: boolean
    inheritedAs?: string
}

export interface Trait {
    id: string
    name: string
    explanation?: string
    traitset_id?: string
    traitsetId?: string
    traitset?: Traitset
    requiredTraits?: Trait[]
    locationRestricted?: boolean
    resource?: boolean
    statement?: string
    notes?: string
    ratingType?: string
    rating?: Die[]
    sfxs?: SFX[]
    defaultTraitSetting?: TraitSetting
    traitSettingId?: string
    traitSetting?: TraitSetting
    subTraits?: Trait[]
    possibleSubTraits?: Trait[]
    possibleSfxs?: SFX[]
    inheritable?: boolean
    entities?: Entity[]
    instances?: string[]
}

export interface TraitInput {
    name?: string
    traitsetId?: string
    statement?: string
    resource?: boolean
    locationsEnabled?: string[]
    locationsDisabled?: string[]
    requiredTraits?: string[]
    locationRestricted?: boolean
    ratingType?: string
    rating?: string[]
    possibleSubTraits?: string[]
    possibleSfxs?: string[]
    available_sfxs?: string[]
    sfxs?: string[]
    inheritable?: boolean
}

export interface Traitset {
    id: string
    name?: string
    explainer?: string
    entityTypes?: string[]
    locationRestricted?: boolean
    limit?: number
    order?: number
    duplicates?: boolean
    traits?: Trait[]
    sfxs?: SFX[]
    defaultTraitSetting?: TraitSetting
    score?: number
}

export interface Relation {
    id: string
    fromEntity: Entity
    toEntity: Entity
    traitsets?: Traitset[]
    favorite?: boolean
}

export interface Image {
    path: string
    ext: string
    width?: number
    height?: number
}

export interface Entity {
    id: string
    key: string
    name: string
    active?: boolean
    description?: string
    image?: Image
    imagened?: boolean
    entityType: string
    location?: Location
    following?: Entity
    followers?: Entity[]
    traitsets?: Traitset[]
    sfxs?: SFX[]
    relations?: Relation[]
    favorite?: boolean
    isArchetype?: boolean
    archetype?: Entity
    instances?: Entity[]
    hidden?: boolean
    knownTo?: Entity[]
}

export interface EntityInput {
    name?: string
    description?: string
    image?: string
    imagened?: boolean
    entityType?: string
    location?: string
    following?: string
    traitsets?: string[]
    sfxs?: string[]
    favorite?: boolean
    isArchetype?: boolean
    archetypeId?: string
    hidden?: boolean
    showTo?: string[]
    knownTo?: string[]
}

export interface Character extends Entity {
    score?: number
    available?: boolean
    pp?: number
}

export interface GMC {
    id: string
    name: string
    traitsets: Traitset[]
}

export interface Location extends Entity {
    parent?: Location
    parents?: Location[]
    flavortext?: string
    entities?: Entity[]
    zones?: Location[]
    transversables?: Location[]
}
