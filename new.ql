/**
 * @name Insecure ephemeral ECC private key generation
 * @description Generating ECC private keys at runtime using ec.generate_private_key() 
 *              typically results in ephemeral keys that are not persisted or protected,
 *              which can lead to loss of private keys or poor key management.
 * @kind problem
 * @problem.severity warning
 * @id py/insecure-ecc-key-generation
 * @tags security
 *       cryptography
 *       key-management
 */

import python
import semmle.python.ApiGraphs
import semmle.python.dataflow.new.DataFlow

from DataFlow::Node keyGenCall
where
  // Detect calls to cryptography.hazmat.primitives.asymmetric.ec.generate_private_key
  keyGenCall = API::moduleImport("cryptography")
                  .getMember("hazmat")
                  .getMember("primitives")
                  .getMember("asymmetric")
                  .getMember("ec")
                  .getMember("generate_private_key")
                  .getACall()

select keyGenCall, 
  "Insecure generation of ECC private key using ec.generate_private_key(). " +
  "This creates an ephemeral key that is usually not persisted securely."
