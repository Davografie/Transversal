from pydantic import BaseModel

class Player(BaseModel):
	id: str
	name: str

class Die(BaseModel):
	id: str
	number_rating: int
	result: int
	is_result: bool
	is_effect: bool

class Rating(BaseModel):
	dice: list[Die]

class TraitSetting(BaseModel):
	id: str
	trait: lambda: Trait
	statement: str
	notes: str
	rating_type: str
	rating: lambda: Rating

class Trait(BaseModel):
	id: str
	name: str

class Location(BaseModel):
	id: str
	key: str