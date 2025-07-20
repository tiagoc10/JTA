Improvements:
- When the path from the city to the state is not found, the code currently returns the exact path that couldn't be resolved. While this may help with debugging, it might not be best  practice. Return the country (level 2), for example, instead.
- Restructure the path comparison logic for better clarity and efficiency.
- Explore alternative pathfinding strategies.
- Consider a different approach for recursive search. The current method uses many recursive lists, which may affect scalability.
- Add unit tests.

Limitations:
- Heavy use of recursion can impact scalability.
- Relies on formatted data (sensitive to spelling and formatting errors).
- Requires normalization of input data (accents, capitalization).