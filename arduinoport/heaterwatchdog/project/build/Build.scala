import sbt._

class HeaterWatchdogProject(info: ProjectInfo) extends DefaultProject(info) {
  val dispatch = "net.databinder" %% "dispatch-http" % "0.7.8"
  val slf4j = "org.slf4j" % "slf4j-api" % "1.6.1"
  val slf4jSimple = "org.slf4j" % "slf4j-simple" % "1.6.1"

  override def filterScalaJars = true
  override val manifestClassPath = Some("scala-library.jar")

  override def mainClass = Some("HeaterWatchdog")

}
