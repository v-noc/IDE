import logging
from typing import List, Optional
from .manager import JediProjectManager

logger = logging.getLogger(__name__)

class MROResolver:
    """
    Resolves Method Resolution Order (MRO) for classes using Jedi.
    """
    def __init__(self, project_manager: JediProjectManager):
        self.project_manager = project_manager

    def resolve_mro(self, file_path: str, source: str, line: int, column: int) -> List[str]:
        """
        Resolve the MRO for a class definition at the given position.
        Returns a list of fully qualified names representing the MRO.
        """
        try:
            script = self.project_manager.get_script(file_path, source)
            
            # Infer the definition at the class name position
            # Note: Jedi uses 1-based lines and 0-based columns
            defs = script.infer(line=line, column=column)
            
            if not defs:
                logger.warning(f"Could not infer definition at {file_path}:{line}:{column}")
                return []

            d_def = defs[0]
            
            # --- WARNING: Private API Usage ---
            # Accessing _name (Jedi Name) -> value (Jedi Context/Value) -> py__mro__
            # This returns a tuple of Jedi Contexts
            mro_qnames = []
            try:
                # The path to the value may differ slightly between Jedi versions.
                # We iterate over inferred values (usually just one for a class def)
                for infer in d_def._name.infer():
                    if hasattr(infer, 'py__mro__'):
                        contexts = infer.py__mro__()
                        
                        # Extract qualified names
                        for c in contexts:
                            qnames = c.name.get_qualified_names()
                            if qnames:
                                mro_qnames.append(".".join(qnames))
                            else:
                                mro_qnames.append(c.name.string_name) # Fallback
                        
                        # We only need the MRO from the first valid inference
                        if mro_qnames:
                            break
            except AttributeError as e:
                logger.warning(f"Could not access internal Jedi MRO API: {e}")
                return []
            except Exception as e:
                logger.error(f"Error resolving MRO: {e}")
                return []
                
            return mro_qnames

        except Exception as e:
            logger.error(f"Failed to resolve MRO for {file_path}: {e}")
            return []
