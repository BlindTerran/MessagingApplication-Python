<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elliptic Example</title>
    <!-- Import Elliptic library -->
    <script src="https://cdn.jsdelivr.net/npm/elliptic@6.5.3/dist/elliptic.min.js"></script>
</head>
<body>
    <h1>Elliptic Example</h1>
    <script>
        // Create an elliptic curve object, selecting the secp256k1 curve
        var ec = new elliptic.ec('secp256k1');

        // Generate key pair
        var keyPair = ec.genKeyPair();

        // Get the public and private keys
        var publicKey = keyPair.getPublic('hex');
        var privateKey = keyPair.getPrivate('hex');

        // Print the public and private keys
        console.log("Public Key:", publicKey);
        console.log("Private Key:", privateKey);
    </script>
</body>
</html>
