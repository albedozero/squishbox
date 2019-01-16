<!DOCTYPE html>
<html>
<title>Squishbox Configuration</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
body {
padding: 8px;
text-align: left;
background-color : #fff;
font-family: medium Verdana, Helvetica, Arial, sans-serif;
font-size: 100%
}

input[type=text], select, textarea {
    padding: 6px 15px;
    margin: 8px 0px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
}

input[type=submit] {
    background-color: #4CAF50;
    width: 120px;
    color: white;
    padding: 8px 15px;
    margin: 8px 0px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
}

input[type=submit]:hover {
    background-color: #999;
}

</style>


<body>

<?php
$dir = "/home/pi/";
if(isset($_POST['restart'])) {
// restart the squishbox to load any changes
    exec("sudo service squishbox restart");
    $content = $_POST['content'];
}
if(isset($_POST['open'])) {
// open the requested file
  $openfile = $_POST['openfile'];
  if ($fh = fopen($dir . $openfile, "r")) {
      $content = fread($fh, filesize($dir . $openfile));
      fclose($fh);
      $savefile = $openfile;
  } else {
      echo "Unable to open " . $openfile;
  }
} elseif(isset($_POST['save'])) {
// save the text box contents in the designated file
    $savefile = $_POST['savefile'];
    $content = $_POST['content'];
    if ($fh = fopen($dir . $savefile, "w")) {
        fwrite($fh, $content);
        chmod($dir . $savefile, 0666);
    } else {
        echo "Unable to write " . $savefile;
    }
} else {
// nothing requested, just open the initial bank
// determine the initial bank from squishbox_settings.yaml
  if ($cfg = yaml_parse_file($dir . "squishbox_settings.yaml")) {
    $openfile = $cfg["initialbank"];
  } else {
// problem with config, try to open that instead
    echo "Configuration file error! Please repair.";
    $openfile = "squishbox_settings.yaml";
  }  
  if ($fh = fopen($dir . $openfile, "r")) {
      $content = fread($fh, filesize($dir . $openfile));
      fclose($fh);
      $savefile = $openfile;
  } else {
      echo "Unable to open " . $openfile;
  }
}
?>

<form action="/index.php" method="post">
    <input type="text" name="savefile" style="width: 100%;"
      value="<?php if(isset($savefile)) {echo $savefile;}?>">
    <input type="submit" name="save" value="Save" style="background-color: #4CAF50;">
    <input type="submit" name="restart" value="Restart" style="background-color: #2E2EFE;">

    <textarea rows=15 id="content" name="content" spellcheck="false" style="width: 100%;"
      ><?php if(isset($content)) {echo $content;}?></textarea>

    <select id="openfile" name="openfile" style="width: 100%;">
<?php
// Get list of config files that could be loaded/edited
if (is_dir($dir)){
  if ($dh = opendir($dir)){
    while (($file = readdir($dh)) !== false){
      if (substr($file,-4) == "yaml") {
        echo '<option value="' . $file . '">' . $file . '</option>';
      }
    }
    closedir($dh);
  }
}
?>
    </select>
    <input type="submit" name="open" value="Open" style="background-color: #8904B1;">
</form>

</body>
</html>
