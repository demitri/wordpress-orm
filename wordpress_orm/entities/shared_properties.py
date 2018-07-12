
# Many of the properties in several of the WordPress entities are the same,
# for example, "include", "exclude", "orderby", "order" in User and Post objects.
# The methods to perform validation are exactly the same in each. This file
# collects shared properties to enable the code be reused. There isn't enough
# overlap for subclassing to make sense in this case.

