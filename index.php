<!DOCTYPE html>
<html>
<title>SquishBox Control Panel</title>
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

.submitButton {
    width: 90px;
    color: white;
    padding: 8px 15px;
    margin: 8px 0px;
    border: none;
    border-radius: 15px;
    cursor: pointer;
}

.submitLink {
    background:none;
    color:blue;
    border:none; 
    padding:0;
    font: inherit;
    cursor: pointer;
    text-decoration: underline;
}

</style>

<body>
<form action='/index.php' method='post'>
<input type='submit' class='submitButton' name="opendir" value='Files' style='background-color: blue;'>
<input type='submit' class='submitButton' name="devices" value='Devices' style='background-color: purple;'>
<input type='submit' class='submitButton' name="restart" value='Restart' style='background-color: red;'>
</form>

<?php
if (isset($_POST['restart'])) {
// restart pressed
  exec("sudo service squishbox restart");
}
if (isset($_POST['save'])) {
// save pressed, save contents to file
  $savefile = $_POST['savefile'];
  $content = $_POST['content'];
  if ($fh = fopen("/home/pi/$savefile", "w")) {
    fwrite($fh, $content);
    chmod("/home/pi/$savefile", 0666);
    echo "Saved $savefile";
  } else {
    echo "Unable to write " . $savefile;
  }
}
if (isset($_POST['delete'])) {
  unlink($deletefile);
}
if (isset($_POST['upload'])) {
  $total = count($_FILES['uploadedfiles']['name']);
  $success = 1;
  for( $i=0 ; $i < $total ; $i++ ) {
    $target = $_FILES['uploadedfiles']['tmp_name'][$i];
    $dest = $_POST['opendir'] . $_FILES['uploadedfiles']['name'][$i];
    if (!move_uploaded_file($target , $dest)) {
      $success=0;
    }
  }
  if ($success==1) {
    echo "Files uploaded.\n";
  } else {
    echo "Some or all files not uploaded.\n";
  }
}
if (isset($_POST['devices'])) {
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
// show connected MIDI devices
  echo '<hr />MIDI Inputs:<pre>';
  system('sudo aconnect -i');
  echo '</pre><hr />MIDI Outputs:<pre>';
  system('sudo aconnect -o');
  echo '</pre><hr />';
  
// File Manager
} elseif (isset($_POST['opendir'])) {
  $pwd = $_POST['opendir'];
  if ($pwd=="Files") {
    $pwd = "/home/pi/";
  }
  if (is_dir($pwd)){
    $cmd = "df -h " . escapeshellarg($pwd);
    $free = preg_split('/\s+/', shell_exec($cmd))[10];
    echo "
$pwd Files:
<span style='float:right;'>
Free Space: $free
</span>
";
    if ($pwd !== "/home/pi/") {
      $dirup = dirname($pwd, 1);
      echo "
<hr /><form action='/index.php' method='post'>
<input type='hidden' name='opendir' value='$dirup/'>
<input type='submit' class='submitLink' name='changedir' value='Up Directory/'>
</form>
";
    }
    if ($dh = opendir($pwd)) {
      while (($file = readdir($dh)) !== false) {
        if (filetype($pwd . $file) == "dir" and 
            substr($file,0,1) !== "." and
            substr($file,0,1) !== "_") {
          echo "
<hr /><form action='/index.php' method='post'>
<input type='hidden' name='opendir' value='$pwd$file/'>
<input type='submit' class='submitLink' name='changedir' value='$file/'>
</form>
";
        } elseif (strtolower(pathinfo($file,PATHINFO_EXTENSION)) == "yaml") {
          echo "
<hr /><form action='/index.php' method='post'>
<input type='submit' class='submitLink' name='openfile' value='$file'>
";
          if ($file !== "squishbox_settings.yaml") {
            echo "
<span style='float:right;'>
<input type='hidden' name='deletefile' value='$pwd$file'>
<input type='submit' class='submitLink' name='delete' value='Delete'
  onclick='return confirm(\"Delete $file?\")'>
</span>
";        
          }
          echo "</form>\n";
        } elseif (strtolower(pathinfo($file,PATHINFO_EXTENSION)) == "sf2") {
          $cmd="du -h " . escapeshellarg($pwd) . escapeshellarg($file);
          $size=preg_split('/\s+/', shell_exec($cmd))[0];
          echo "
<hr /><form action='/index.php' method='post'>
$file
<span style='float:right;'>
($size) ..
<input type='hidden' name='deletefile' value='$pwd$file'>
<input type='submit' class='submitLink' name='delete' value='Delete'
  onclick='return confirm(\"Delete $file?\")'>
</span></form>
";
        }
      }
      closedir($dh);
    }
    echo "
<hr />
<form action='/index.php' method='post' enctype='multipart/form-data'>
<input type='hidden' name='opendir' value='$pwd'>
<input type='submit' class='submitButton' name='upload' value='Upload' style='background-color: green;'>
<input type='file' name='uploadedfiles[]' multiple>
</form>
";
  }
} else {
  
// open a file for the editor
  if (isset($_POST['openfile'])) {
    $openfile = $_POST['openfile'];
  } elseif (isset($savefile)) {
    $openfile = $savefile;
  } elseif ($cfg = yaml_parse_file("/home/pi/squishbox_settings.yaml")) {
    $openfile = $cfg['initialbank'];
  } else {
    echo "Configuration file error! Please repair.";
    $openfile = "squishbox_settings.yaml";
  }
  if ($fh = fopen("/home/pi/$openfile", "r")) {
    $content = fread($fh, filesize("/home/pi/$openfile"));
    fclose($fh);
    
// Editor
    echo "
<form action='/index.php' method='post'>
<input type='text' name='savefile' style='width: 100%;' value='$openfile'>

<textarea rows=15 id='content' name='content' spellcheck='false' style='width: 100%;'>
$content
</textarea>

<input type='submit' class='submitButton' name='save' value='Save' style='background-color: green;'>
</form>
";
  } else {
    echo "Unable to open $openfile";
  }
}
?>

</body>
</html>
